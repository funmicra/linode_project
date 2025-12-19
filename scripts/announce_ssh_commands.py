#!/usr/bin/env python3

import json
import subprocess
import sys

TERRAFORM_DIR = "terraform"
SSH_USER = "funmicra"


def tf_output(args):
    cmd = ["terraform", f"-chdir={TERRAFORM_DIR}", "output"] + args
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except subprocess.CalledProcessError:
        print(f"[ERROR] Failed to run: {' '.join(cmd)}")
        sys.exit(1)


def main():
    # Read Terraform outputs
    proxy_ip = tf_output(["-raw", "proxy_public_ip"])
    private_ips_raw = tf_output(["-json", "private_ips"])

    private_ips = json.loads(private_ips_raw)

    print("\nAccess your private Linodes using the following SSH commands:\n")

    for idx, ip in enumerate(private_ips):
        print(f"ssh -J {SSH_USER}@{proxy_ip} {SSH_USER}@{ip}   # private-{idx}")

    print("")


if __name__ == "__main__":
    main()
