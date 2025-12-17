#!/usr/bin/env python3
import json
import subprocess

# Get Terraform outputs
def tf_output(name, json=False):
    cmd = ["terraform", "output"]
    if json:
        cmd.append("-json")
    cmd.append(name)
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

# Read outputs
proxy_ip = tf_output("proxy_public_ip")
private_ips_json = tf_output("private_ips", json=True)
private_ips = json.loads(private_ips_json)  # this gives a list of strings

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
