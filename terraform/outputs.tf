output "gateway_public_ip" {
  description = "Public IPv4 of the gateway instance"
  value       = tolist(linode_instance.gateway.ipv4)[0]
}

output "private_ips" {
  description = "Private IPs of workload nodes"
  value       = [
    for i in linode_instance.private : i.interface[0].ipv4[0].vpc
  ]
}

output "gateway_id" {
  value = linode_instance.gateway.id
}

output "instance_ids" {
  value = [
    for vm in linode_instance.private : vm.id
  ]
}




