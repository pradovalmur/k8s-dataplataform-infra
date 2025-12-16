variable "cluster_name" {
  type        = string
  description = "Nome lógico do cluster (prefixo para recursos)."
}

variable "location" {
  type        = string
  default     = "nbg1"
  description = "Localização Hetzner (por ex: nbg1, fsn1, hel1)."
}

variable "image" {
  type        = string
  default     = "ubuntu-22.04"
  description = "Imagem base para os servidores."
}

variable "master_server_type" {
  type        = string
  default     = "cpx21"
  description = "Flavor das VMs master."
}

variable "worker_server_type" {
  type        = string
  default     = "cpx21"
  description = "Flavor das VMs worker."
}

variable "master_count" {
  type        = number
  default     = 1
  description = "Quantidade de masters."
}

variable "worker_count" {
  type        = number
  default     = 2
  description = "Quantidade de workers."
}

variable "ssh_key_ids" {
  type        = list(string)
  description = "Lista de IDs de SSH keys já cadastradas no projeto Hetzner."
}

variable "network_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR da network privada."
}

variable "subnet_cidr" {
  type        = string
  default     = "10.0.1.0/24"
  description = "CIDR da subnet usada pelos nodes."
}

variable "network_zone" {
  type        = string
  default     = "eu-central"
  description = "Network zone da Hetzner (ex.: eu-central)."
}

variable "firewall_ids" {
  description = "Lista de IDs de firewalls Hetzner a associar aos servidores"
  type        = list(number)
  default     = []
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels extras para todos os recursos."
}