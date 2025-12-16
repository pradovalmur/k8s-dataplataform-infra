variable "hcloud_token" {
  type        = string
  description = "API token da Hetzner."
  sensitive   = true
}

variable "ip_cidr" {
  type = string
}
