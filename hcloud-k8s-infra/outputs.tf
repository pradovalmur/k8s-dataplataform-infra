output "master_public_ips" {
  value = module.hcloud_cluster.master_public_ips
}

output "worker_public_ips" {
  value = module.hcloud_cluster.worker_public_ips
}

output "master_private_ips" { 
  value = module.hcloud_cluster.master_private_ips 
  }

output "worker_private_ips" { 
  value = module.hcloud_cluster.worker_private_ips
   }

output "network_id" {
  value       = module.hcloud_cluster.network_id
}