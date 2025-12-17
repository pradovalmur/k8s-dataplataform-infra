
terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }
}

locals {
  nodeport_cidrs = var.lb_ipv4 != null ? ["${var.lb_ipv4}/32"] : var.admin_cidrs
}

resource "hcloud_firewall" "this" {
  name = var.name

  # SSH
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = var.admin_cidrs
  }

  # Kubernetes API
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "6443"
    source_ips = var.admin_cidrs
  }

  # etcd (se houver etcd nos nós)
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "2379-2380"
    source_ips = [var.network_cidr]
  }

  # kubelet
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "10250"
    source_ips = concat([var.network_cidr], var.admin_cidrs)
  }

  # kube-scheduler
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "10259"
    source_ips = [var.network_cidr]
  }

  # kube-controller-manager
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "10257"
    source_ips = [var.network_cidr]
  }

  # Calico BGP (dependendo do modo)
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "179"
    source_ips = [var.network_cidr]
  }

  # Calico VXLAN (se usando VXLAN)
  rule {
    direction  = "in"
    protocol   = "udp"
    port       = "4789"
    source_ips = [var.network_cidr]
  }

  # NodePort (opcional)
  dynamic "rule" {
    for_each = var.allow_nodeport ? [1] : []
    content {
      direction  = "in"
      protocol   = "tcp"
      port       = "30000-32767"
      source_ips = local.nodeport_cidrs
    }
  }
}

resource "hcloud_firewall_attachment" "this" {
  for_each    = length(var.server_ids) > 0 ? { "all" = true } : {}
  firewall_id = hcloud_firewall.this.id
  server_ids  = var.server_ids
}