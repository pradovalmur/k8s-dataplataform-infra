variable "hcloud_token" {
  type        = string
  description = "API token da Hetzner."
  sensitive   = true
}

variable "ip_cidr" {
  type = string
}

variable "firewall_name" {
  type    = string
  default = "k8s-firewall"
}

variable "network_cidr" {
  type = string
}

variable "admin_cidrs" {
  type = list(string)
}

variable "firewall_rules" {
  description = "Regras do firewall (passadas para o módulo)"
  type = list(object({
    direction  = string
    protocol   = string
    port       = string
    source_ips = list(string)
  }))
  default = []
}

variable "allow_nodeport" {
  type    = bool
  default = true
}

variable "nodeport_source_cidrs" {
  type    = list(string)
  default = []
}

variable "lb_ipv4" {
  type    = string
  default = null
}

# se você já tem servers no root, normalmente você já tem algo assim
variable "server_ids" {
  type    = list(string)
  default = []
}
