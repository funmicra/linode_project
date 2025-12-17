# ------------------------
# Provider
# ------------------------
terraform {
  required_providers {
    linode = {
      source  = "linode/linode"
      version = "3.6.0"
    }
  }
}

provider "linode" {
  token = var.linode_token
}

# ------------------------
# VPC and Subnet
# ------------------------
resource "linode_vpc" "private" {
  label  = "private-vpc"
  region = var.region
}

resource "linode_vpc_subnet" "private" {
  label  = "private-subnet"
  vpc_id = linode_vpc.private.id
  ipv4   = "192.168.33.0/24"
}

# ------------------------
# Proxy Linode
# ------------------------
resource "linode_instance" "proxy" {
  label  = "vpc-forward-proxy"
  region = var.region
  type   = "g6-nanode-1"
  image  = "linode/ubuntu24.04"

  stackscript_id   = var.proxy_stackscript_id
  stackscript_data = {
    username = var.deploy_user
    user_password  = var.user_password
    ssh_key_b64 = file("ssh_key.b64")
  }

  # Public interface
  interface {
    purpose = "public"
  }

  # VPC interface with fixed IP
  interface {
    purpose = "vpc"
    subnet_id = linode_vpc_subnet.private.id
    
    ipv4 {
        vpc = "192.168.33.250"
    }
  }

  tags = ["gateway", "vpc", "edge"]
}

# ------------------------
# Private Linodes
# ------------------------
resource "linode_instance" "private" {
  count  = var.private_count
  label  = "private-${count.index}"
  region = var.region
  type   = "g6-standard-1"
  image  = "linode/ubuntu24.04"

  stackscript_id   = var.private_stackscript_id
  stackscript_data = {
    username   = var.deploy_user
    user_password  = var.user_password
    ssh_key_b64   = file("ssh_key.b64")
    }

  interface {
    purpose   = "vpc"
    subnet_id = linode_vpc_subnet.private.id

    ipv4 {
      vpc = "192.168.33.${10 + count.index}"
    }
  }

  tags = ["private", "workload"]
}


# ------------------------
# Outputs
# ------------------------
output "proxy_public_ip" {
  description = "Public IPv4 of the proxy instance"
  value       = tolist(linode_instance.proxy.ipv4)[0]
}

output "private_ips" {
  description = "Private IPs of workload nodes"
  value       = [
    for i in linode_instance.private : i.interface[0].ipv4[0].vpc
  ]
}

output "proxy_id" {
  value = linode_instance.proxy.id
}

output "instance_ids" {
  value = [
    for vm in linode_instance.private : vm.id
  ]
}

# ------------------------
# Variables
# ------------------------
variable "linode_token" {
  sensitive   = true
}

variable "region" {
  default = "de-fra-2"
}

variable "proxy_stackscript_id" {
  default = 1975956
}

variable "private_stackscript_id" {
  default = 1975967
}

variable "deploy_user" {
  default = "funmicra"
}

variable "private_count" {
  default = 2
}

variable "user_password" {
  type      = string
  sensitive = true
}