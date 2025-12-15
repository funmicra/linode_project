resource "linode_vpc" "private" {
  label  = "private-vpc"
  region = var.region
}

resource "linode_vpc_subnet" "private" {
  label      = "private-subnet"
  vpc_id     = linode_vpc.private.id
  ipv4       = "192.168.33.0/24"
}


resource "linode_instance" "gateway" {
  label  = "vpc-gateway"
  region = var.region
  type   = "g6-nanode-1"
  image  = "linode/ubuntu24.04"

  authorized_keys = split("\n", trimspace(file(var.ssh_keys_file)))


  interface {
    purpose = "public"
  }

  interface {
    purpose = "vpc"
    subnet_id = linode_vpc_subnet.private.id
  }

  tags = ["gateway", "edge", "vpc"]
}

resource "linode_instance" "private" {
  count  = 2
  label  = "private-${count.index}"
  region = var.region
  type   = "g6-standard-1"
  image  = "linode/ubuntu22.04"

  authorized_keys = split("\n", trimspace(file(var.ssh_keys_file)))


  interface {
    purpose = "vpc"
    subnet_id = linode_vpc_subnet.private.id

    ipv4 {
      vpc = "192.168.33.${10 + count.index}"
    }
  }

  tags = ["private", "workload"]
}
