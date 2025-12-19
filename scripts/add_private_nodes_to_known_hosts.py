#!/usr/bin/env python3

import os
import subprocess
import pwd
import grp

HOSTS_FILE = "ansible/inventory/hosts.ini"
SSH_DIR = "/var/lib/jenkins/.ssh"
KNOWN_HOSTS = os.path.join(SSH_DIR, "known_hosts")
JENKINS_USER = "jenkins"
JENKINS_GROUP = "jenkins"
PROXY_USER = "funmicra"


def run(cmd, ignore_errors=False):
    try:
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError:
        if not ignore_errors:
            raise
        print(f"[WARN] Ignored failure: {' '.join(cmd)}")


def parse_inventory(section):
    ips = []
    capture = False

    with open(HOSTS_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("["):
                capture = line == f"[{section}]"
                continue
            if capture and line:
                ips.append(line)

    return ips


def ensure_ssh_dir():
    os.makedirs(SSH_DIR, exist_ok=True)


def fix_ownership(path):
    uid = pwd.getpwnam(JENKINS_USER).pw_uid
    gid = grp.getgrnam(JENKINS_GROUP).gr_gid
    os.chown(path, uid, gid)


def main():
    proxy_ips = parse_inventory("proxy")
    private_ips = parse_inventory("private")

    if not proxy_ips:
        raise RuntimeError("No proxy IP found in inventory")

    proxy_ip = proxy_ips[0]
    print(f"[INFO] Using proxy: {proxy_ip}")

    if not private_ips:
        print("[INFO] No private nodes found, exiting")
        return

    ensure_ssh_dir()

    with open(KNOWN_HOSTS, "a") as kh:
        for ip in private_ips:
            print(f"[INFO] Processing private node: {ip}")

            run(["ssh-keygen", "-R", ip], ignore_errors=True)

            subprocess.run(
                [
                    "ssh-keyscan",
                    "-o", f"ProxyJump={PROXY_USER}@{proxy_ip}",
                    "-H",
                    ip
                ],
                stdout=kh,
                stderr=subprocess.DEVNULL,
                check=False
            )

    fix_ownership(KNOWN_HOSTS)
    print("[INFO] known_hosts updated for private nodes")


if __name__ == "__main__":
    main()
