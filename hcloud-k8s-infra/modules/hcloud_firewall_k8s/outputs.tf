output "id" {
  description = "ID do firewall"
  value       = hcloud_firewall.this.id
}

output "name" {
  description = "Nome do firewall"
  value       = hcloud_firewall.this.name
}
