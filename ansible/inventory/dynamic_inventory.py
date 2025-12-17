#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

ANSIBLE_USER = "funmicra"

SCRIPT_DIR = Path(__file__).resolve().parent
TF_DIR = (SCRIPT_DIR / "../../terraform").resolve()
OUTPUT_FILE = SCRIPT_DIR / "hosts.ini"

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def tf_output(name, json_output=False):
    cmd = ["terraform", f"-chdir={TF_DIR}", "output"]
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
        print(f"[ERROR] terraform output '{name}' failed", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

    out = result.stdout.strip()
    return json.loads(out) if json_output else out

def normalize_ip(value):
    """
    Ensure the IP is a clean string with no quotes or whitespace.
    """
    if not value:
        return ""
    return str(value).strip().strip('"').strip("'")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    if not TF_DIR.exists():
        print(f"[ERROR] Terraform directory not found: {TF_DIR}", file=sys.stderr)
        sys.exit(1)

    proxy_ip_raw = tf_output("proxy_public_ip")
    private_ips_raw = tf_output("private_ips", json_output=True)

    proxy_ip = normalize_ip(proxy_ip_raw)

    if not proxy_ip:
        print("[ERROR] proxy_public_ip is empty", file=sys.stderr)
        sys.exit(1)

    if not isinstance(private_ips_raw, list) or not private_ips_raw:
        print("[ERROR] private_ips must be a non-empty list", file=sys.stderr)
        sys.exit(1)

    private_ips = [normalize_ip(ip) for ip in private_ips_raw if normalize_ip(ip)]

    if not private_ips:
        print("[ERROR] private_ips resolved to empty after normalization", file=sys.stderr)
        sys.exit(1)

    inventory = [
        "[proxy]",
        proxy_ip,
        "",
        "[proxy:vars]",
        f"ansible_user={ANSIBLE_USER}",
        "",
        "[private]",
        *private_ips,
        "",
        "[private:vars]",
        f"ansible_user={ANSIBLE_USER}",
        f"ansible_ssh_common_args=-o ProxyJump={ANSIBLE_USER}@{proxy_ip} -o ForwardAgent=yes -o StrictHostKeyChecking=no",
        "",
    ]

    OUTPUT_FILE.write_text("\n".join(inventory))
    print(f"[OK] Static inventory written to {OUTPUT_FILE}")

# ------------------------------------------------------------------

if __name__ == "__main__":
    main()
