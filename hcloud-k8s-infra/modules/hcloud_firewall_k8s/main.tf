terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }
}

locals {
  nodeport_cidrs = (
    length(var.nodeport_source_cidrs) > 0 ? var.nodeport_source_cidrs :
    (var.lb_ipv4 != null ? ["${var.lb_ipv4}/32"] : var.admin_cidrs)
  )

  all_rules = concat(
    var.rules,
    var.allow_nodeport ? [{
      direction  = "in"
      protocol   = "tcp"
      port       = "30000-32767"
      source_ips = local.nodeport_cidrs
    }] : []
  )
}

resource "hcloud_firewall" "this" {
  name = var.name

  dynamic "rule" {
    for_each = local.all_rules
    content {
      direction  = rule.value.direction
      protocol   = rule.value.protocol
      port       = rule.value.port
      source_ips = rule.value.source_ips
    }
  }
}

resource "hcloud_firewall_attachment" "this" {
  for_each    = length(var.server_ids) > 0 ? toset(var.server_ids) : toset([])
  firewall_id = hcloud_firewall.this.id
  server_ids   = each.value
}
