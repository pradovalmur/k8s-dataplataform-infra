variable "name" {
  description = "Nome do firewall"
  type        = string
}

variable "network_cidr" {
  description = "CIDR da rede privada do cluster (ex: 10.0.0.0/16)"
  type        = string
}

variable "admin_cidrs" {
  description = "Lista de CIDRs permitidos para SSH/API (ex: [\"203.0.113.10/32\"])"
  type        = list(string)
}

variable "allow_nodeport" {
  description = "Se true, libera NodePort (30000-32767) a partir de admin_cidrs"
  type        = bool
  default     = true
}

variable "nodeport_source_cidrs" {
  description = "Opcional: CIDRs para NodePort. Se vazio e allow_nodeport=true, usa admin_cidrs."
  type        = list(string)
  default     = []
}

variable "lb_ipv4" {
  type        = string
  description = "IPv4 do Load Balancer (ex: 91.98.5.155)"
  default     = null
}

variable "server_ids" {
  description = "IDs dos servers que terão esse firewall aplicado"
  type        = list(string)
  default     = []
}