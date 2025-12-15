variable "linode_token" {
  description = "Linode API token"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "Linode region"
  type        = string
  default     = "de-fra-2"
}

variable "ssh_keys_file" {
  description = "Path to file containing SSH public keys, one per line"
  type        = string
}
