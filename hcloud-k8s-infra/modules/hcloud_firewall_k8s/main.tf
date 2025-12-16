
terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }
}


locals {
  nodeport_cidrs = length(var.nodeport_source_cidrs) > 0 ? var.nodeport_source_cidrs : var.admin_cidrs
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
    source_ips = [var.network_cidr]
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
