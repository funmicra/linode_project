#!/usr/bin/env python3
import json
import subprocess
import os

# Path to your Terraform root folder
TF_DIR = os.path.join(os.path.dirname(__file__), "../../terraform")

# Get Terraform outputs
def tf_output(name, as_json=False):
    cmd = ["terraform", f"-chdir={TF_DIR}", "output"]
    if as_json:
        cmd.append("-json")
    cmd.append(name)
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout) if as_json else result.stdout.strip()

# Read outputs
proxy_ip = tf_output("proxy_public_ip")
private_ips = tf_output("private_ips", as_json=True)

# Build inventory
inventory = {
    "proxy": {
        "hosts": [proxy_ip],
        "vars": {
            "ansible_user": "funmmicra"
        }
    },
    "private": {
        "hosts": private_ips,
        "vars": {
            "ansible_user": "funmmicra",
            "ansible_ssh_common_args": f"-o ProxyJump=funmmicra@{proxy_ip}",
            "PROXY_IP": proxy_ip
        }
    },
    "_meta": {"hostvars": {}}
}

print(json.dumps(inventory))
