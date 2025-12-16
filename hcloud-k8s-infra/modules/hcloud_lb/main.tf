
terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }
}


resource "hcloud_load_balancer" "this" {
  name               = var.name
  load_balancer_type = var.load_balancer_type

  # escolha um dos dois (location ou network_zone). Se você já usa location (ex: nbg1), mantenha.
  location     = var.location
  network_zone = var.network_zone

  labels = var.labels
}

resource "hcloud_load_balancer_target" "servers" {
  for_each         = var.servers
  type             = "server"
  load_balancer_id = hcloud_load_balancer.this.id
  server_id        = each.value
}

resource "hcloud_load_balancer_service" "services" {
  for_each         = { for s in var.services : s.name => s }
  load_balancer_id = hcloud_load_balancer.this.id

  protocol         = each.value.protocol
  listen_port      = each.value.listen_port
  destination_port = each.value.destination_port

  proxyprotocol = try(each.value.proxyprotocol, false)
}
