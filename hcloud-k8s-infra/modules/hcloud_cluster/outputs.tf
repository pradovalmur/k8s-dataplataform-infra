output "master_public_ips" {
  description = "IPs públicos dos masters."
  value       = [for s in hcloud_server.master : s.ipv4_address]
}

output "worker_public_ips" {
  description = "IPs públicos dos workers."
  value       = [for s in hcloud_server.worker : s.ipv4_address]
}

output "master_private_ips" {
  description = "IPs privados dos masters na network do cluster."
  value       = [for n in hcloud_server_network.master_net : n.ip]
}

output "worker_private_ips" {
  description = "IPs privados dos workers na network do cluster."
  value       = [for n in hcloud_server_network.worker_net : n.ip]
}

output "network_id" {
  description = "ID da network privada."
  value       = hcloud_network.this.id
}
