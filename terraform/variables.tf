variable "linode_token" {
  description = "Linode API token"
  sensitive   = true
}

variable "region" {
  description = "Linode region"
  type        = string
  default     = "de-fra-2"
}

variable "ssh_keys_file" {
  description = "Path to SSH public key"
}
