#!/usr/bin/env python3

import os
import subprocess
import sys
import time
from pathlib import Path


TERRAFORM_DIR = Path("terraform")


def run(cmd, cwd=None):
    print(f"[INFO] Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def require_env(var):
    if not os.environ.get(var):
        print(f"[ERROR] Required env var missing: {var}")
        sys.exit(1)


def main():
    # Validate required Terraform variables
    required_envs = [
        "TF_VAR_linode_token",
        "TF_VAR_ssh_keys_file",
        "TF_VAR_user_password",
        "TF_VAR_username",
    ]

    for env in required_envs:
        require_env(env)

    if not TERRAFORM_DIR.exists():
        print("[ERROR] terraform/ directory not found")
        sys.exit(1)

    # Terraform init & apply
    run(["terraform", "init"], cwd=TERRAFORM_DIR)
    run(["terraform", "apply", "-auto-approve"], cwd=TERRAFORM_DIR)

    print("[INFO] Waiting for resources to stabilize...")
    time.sleep(10)

    print("[INFO] Terraform apply completed successfully")


if __name__ == "__main__":
    main()
