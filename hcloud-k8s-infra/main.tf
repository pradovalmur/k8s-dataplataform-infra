terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }

  required_version = ">= 1.5.0"
}

provider "hcloud" {
  token = var.hcloud_token
}

module "firewall" {
  source = "./modules/hcloud_firewall_k8s"

  name         = var.firewall_name
  network_cidr = var.network_cidr
  admin_cidrs  = var.admin_cidrs

  rules = var.firewall_rules

  allow_nodeport        = var.allow_nodeport
  nodeport_source_cidrs = var.nodeport_source_cidrs
  lb_ipv4               = var.lb_ipv4

  server_ids = var.server_ids
}

module "lb_traefik" {
  source   = "./modules/hcloud_lb"
  name     = "k8s-lab-traefik"
  location = "nbg1"

  servers = module.hcloud_cluster.server_id_map

  services = [
    { name = "http",  protocol = "tcp", listen_port = 80,  destination_port = 30080 },
    { name = "https", protocol = "tcp", listen_port = 443, destination_port = 30443 }
  ]
}

resource "hcloud_ssh_key" "local_key" {
  name       = "local-ed25519"
  public_key = file("~/.ssh/id_ed25519.pub")
}

module "hcloud_cluster" {
  source = "./modules/hcloud_cluster"

  cluster_name        = "k8s-lab"
  location            = "nbg1"
  image               = "ubuntu-22.04"
  master_server_type  = "cpx21"
  worker_server_type  = "cpx21"
  master_count        = 1
  worker_count        = 2
  ssh_key_ids         = [hcloud_ssh_key.local_key.id]
  network_cidr        = "10.0.0.0/16"
  subnet_cidr         = "10.0.1.0/24"
  network_zone        = "eu-central"

  firewall_ids        = [module.firewall.id]

  labels = {
    environment = "lab"
    project     = "k8s-platform"
  }
}

resource "local_file" "ansible_inventory" {
  filename = abspath("${path.root}/../ansible/inventory.ini")
  content  = <<-EOT
[master]
k8s-lab-master-1 ansible_host=${module.hcloud_cluster.master_public_ips[0]} private_ip=${module.hcloud_cluster.master_private_ips[0]}

[workers]
k8s-lab-worker-1 ansible_host=${module.hcloud_cluster.worker_public_ips[0]} private_ip=${module.hcloud_cluster.worker_private_ips[0]}
k8s-lab-worker-2 ansible_host=${module.hcloud_cluster.worker_public_ips[1]} private_ip=${module.hcloud_cluster.worker_private_ips[1]}

[all:vars]
ansible_user=root
ansible_become=true
ansible_ssh_private_key_file=~/.ssh/id_ed25519
  EOT
}

