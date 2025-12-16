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

output "master_server_ids" {
  description = "IDs dos servers master."
  value       = [for s in hcloud_server.master : s.id]
}

output "worker_server_ids" {
  description = "IDs dos servers worker."
  value       = [for s in hcloud_server.worker : s.id]
}

output "all_server_ids" {
  description = "IDs de todos os servers (master + worker)."
  value       = concat(
    [for s in hcloud_server.master : s.id],
    [for s in hcloud_server.worker : s.id]
  )
}

output "server_id_map" {
  description = "Mapa nome => id de todos os servers"
  value = merge(
    { for s in hcloud_server.master : s.name => s.id },
    { for s in hcloud_server.worker : s.name => s.id }
  )
}
