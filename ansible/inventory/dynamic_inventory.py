#!/usr/bin/env python3
import json
import subprocess
import os
import sys
from pathlib import Path

# --- Configuration -------------------------------------------------

ANSIBLE_USER = "funmicra"

SCRIPT_DIR = Path(__file__).resolve().parent
TF_DIR = (SCRIPT_DIR / "../../terraform").resolve()
OUTPUT_FILE = SCRIPT_DIR / "hosts.ini"

# --- Helpers -------------------------------------------------------

def tf_output(name, json_output=False):
    cmd = [
        "terraform",
        f"-chdir={TF_DIR}",
        "output",
    ]
    if json_output:
        cmd.append("-json")
    cmd.append(name)

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] terraform output {name} failed:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

    return json.loads(result.stdout) if json_output else result.stdout.strip()

# --- Main logic ----------------------------------------------------

def main():
    if not TF_DIR.exists():
        print(f"[ERROR] Terraform directory not found: {TF_DIR}", file=sys.stderr)
        sys.exit(1)

    proxy_ip = tf_output("proxy_public_ip")
    private_ips = tf_output("private_ips", json_output=True)

    if not proxy_ip:
        print("[ERROR] proxy_public_ip is empty", file=sys.stderr)
        sys.exit(1)

    if not private_ips:
        print("[ERROR] private_ips is empty", file=sys.stderr)
        sys.exit(1)

    inventory_lines = []

    # Proxy group
    inventory_lines.append("[proxy]")
    inventory_lines.append(proxy_ip)
    inventory_lines.append("")
    inventory_lines.append("[proxy:vars]")
    inventory_lines.append(f"ansible_user={ANSIBLE_USER}")
    inventory_lines.append("")

    # Private group
    inventory_lines.append("[private]")
    inventory_lines.extend(private_ips)
    inventory_lines.append("")
    inventory_lines.append("[private:vars]")
    inventory_lines.append(f"ansible_user={ANSIBLE_USER}")
    inventory_lines.append(
        f"ansible_ssh_common_args=-o ProxyJump={ANSIBLE_USER}@{proxy_ip}"
    )
    inventory_lines.append("")

    OUTPUT_FILE.write_text("\n".join(inventory_lines))

    print(f"[OK] Static inventory written to {OUTPUT_FILE}")

# --- Entry point ---------------------------------------------------

if __name__ == "__main__":
    main()
