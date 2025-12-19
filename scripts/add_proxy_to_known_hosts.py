#!/usr/bin/env python3

import os
import subprocess
import sys
import pwd
import grp

HOSTS_FILE = "ansible/inventory/hosts.ini"
SSH_DIR = "/var/lib/jenkins/.ssh"
KNOWN_HOSTS = os.path.join(SSH_DIR, "known_hosts")
JENKINS_USER = "jenkins"
JENKINS_GROUP = "jenkins"


def run(cmd, ignore_errors=False):
    try:
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            raise
        print(f"[WARN] Command failed but ignored: {' '.join(cmd)}")


def get_proxy_ip():
    with open(HOSTS_FILE) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.strip() == "[proxy]" and i + 1 < len(lines):
            return lines[i + 1].strip()

    raise RuntimeError("Proxy IP not found in hosts.ini")


def ensure_ssh_dir():
    os.makedirs(SSH_DIR, exist_ok=True)


def fix_ownership(path):
    uid = pwd.getpwnam(JENKINS_USER).pw_uid
    gid = grp.getgrnam(JENKINS_GROUP).gr_gid
    os.chown(path, uid, gid)


def main():
    proxy_ip = get_proxy_ip()
    print(f"[INFO] Proxy IP detected: {proxy_ip}")

    ensure_ssh_dir()

    run(["ssh-keygen", "-R", proxy_ip], ignore_errors=True)

    with open(KNOWN_HOSTS, "a") as kh:
        subprocess.run(
            ["ssh-keyscan", "-H", proxy_ip],
            stdout=kh,
            stderr=subprocess.DEVNULL,
            check=False
        )

    fix_ownership(KNOWN_HOSTS)
    print("[INFO] known_hosts updated successfully")


if __name__ == "__main__":
    main()
