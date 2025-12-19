#!/usr/bin/env python3

import os
import subprocess
import time
import sys

HOSTS_FILE = "ansible/inventory/hosts.ini"
PLAYBOOK = "ansible/site.yaml"
SSH_DIR = "/var/lib/jenkins/.ssh"
KNOWN_HOSTS = os.path.join(SSH_DIR, "known_hosts")


def run(cmd, env=None, check=True):
    subprocess.run(cmd, env=env, check=check)


def parse_inventory(section):
    values = []
    capture = False

    with open(HOSTS_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("["):
                capture = line == f"[{section}]"
                continue
            if capture and line:
                values.append(line)

    return values


def start_ssh_agent():
    result = subprocess.check_output(["ssh-agent", "-s"], text=True)
    for line in result.splitlines():
        if line.startswith("SSH_AUTH_SOCK") or line.startswith("SSH_AGENT_PID"):
            key, val = line.split(";")[0].split("=")
            os.environ[key] = val
    print("[INFO] ssh-agent started")


def add_private_key(key_path):
    run(["ssh-add", key_path])
    print("[INFO] SSH key added to agent")


def trust_proxy(proxy_ip):
    os.makedirs(SSH_DIR, exist_ok=True)
    with open(KNOWN_HOSTS, "a") as kh:
        subprocess.run(
            ["ssh-keyscan", "-H", proxy_ip],
            stdout=kh,
            stderr=subprocess.DEVNULL,
            check=False
        )
    print(f"[INFO] Proxy {proxy_ip} added to known_hosts")


def wait_for_ssh(proxy_user, proxy_ip, user, target_ip):
    print(f"[INFO] Waiting for SSH on {target_ip} via {proxy_ip}")
    while True:
        result = subprocess.run(
            [
                "ssh",
                "-o", "ConnectTimeout=15",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ServerAliveInterval=5",
                "-J", f"{proxy_user}@{proxy_ip}",
                f"{user}@{target_ip}",
                "echo ok"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            print(f"[INFO] {target_ip} is reachable")
            return
        print("[INFO] SSH not ready, retrying in 10s...")
        time.sleep(10)


def run_playbook(ansible_user):
    run([
        "ansible-playbook",
        PLAYBOOK,
        "-i", HOSTS_FILE,
        "-u", ansible_user,
        "-vv"
    ])
    print("[INFO] Ansible playbook completed")


def main():
    ansible_key = os.environ.get("ANSIBLE_PRIVATE_KEY")
    ansible_user = os.environ.get("ANSIBLE_USER")


    if not ansible_key or not ansible_user:
        print("[ERROR] Missing ANSIBLE_PRIVATE_KEY or ANSIBLE_USER")
        sys.exit(1)

    proxy_ips = parse_inventory("proxy")
    private_ips = parse_inventory("private")

    if not proxy_ips:
        print("[ERROR] No proxy defined in inventory")
        sys.exit(1)

    proxy_ip = proxy_ips[0]

    start_ssh_agent()
    add_private_key(ansible_key)
    trust_proxy(proxy_ip)

    for ip in private_ips:
        wait_for_ssh(ansible_user, proxy_ip, ansible_user, ip)

    run_playbook(ansible_user)


if __name__ == "__main__":
    main()