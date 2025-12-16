
terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }
}


# REDE PRIVADA
resource "hcloud_network" "this" {
  name     = "${var.cluster_name}-network"
  ip_range = var.network_cidr

  labels = merge(
    {
      "cluster" = var.cluster_name
    },
    var.labels
  )
}

resource "hcloud_network_subnet" "this" {
  type         = "cloud"
  network_id   = hcloud_network.this.id
  network_zone = var.network_zone
  ip_range     = var.subnet_cidr
}

# MASTER NODES
resource "hcloud_server" "master" {
  count       = var.master_count
  name        = "${var.cluster_name}-master-${count.index + 1}"
  server_type = var.master_server_type
  image       = var.image
  location    = var.location

  ssh_keys = var.ssh_key_ids

  firewall_ids = var.firewall_ids

  labels = merge(
    {
      "cluster" = var.cluster_name
      "role"    = "master"
    },
    var.labels
  )

}

resource "hcloud_server_network" "master_net" {
  count     = var.master_count
  server_id = hcloud_server.master[count.index].id
  network_id = hcloud_network.this.id
  ip        = cidrhost(var.subnet_cidr, 10 + count.index)
}

# WORKER NODES
resource "hcloud_server" "worker" {
  count       = var.worker_count
  name        = "${var.cluster_name}-worker-${count.index + 1}"
  server_type = var.worker_server_type
  image       = var.image
  location    = var.location

  ssh_keys = var.ssh_key_ids

  firewall_ids = var.firewall_ids

  labels = merge(
    {
      "cluster" = var.cluster_name
      "role"    = "worker"
    },
    var.labels
  )

}

resource "hcloud_server_network" "worker_net" {
  count      = var.worker_count
  server_id  = hcloud_server.worker[count.index].id
  network_id = hcloud_network.this.id
  ip         = cidrhost(var.subnet_cidr, 20 + count.index)
}
