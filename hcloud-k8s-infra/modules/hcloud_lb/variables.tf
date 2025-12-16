variable "name" {
  type = string
}

variable "location" {
  type    = string
  default = null
}

variable "network_zone" {
  type    = string
  default = null
}

variable "load_balancer_type" {
  type    = string
  default = "lb11"
}

variable "labels" {
  type    = map(string)
  default = {}
}

# targets (servers)
variable "servers" {
  description = "Mapa de servers a anexar no LB: { nome => id }"
  type        = map(string)
}

# services
variable "services" {
  description = "Lista de serviços do LB"
  type = list(object({
    name             = string
    protocol         = string # tcp/http/https (recomendo tcp pra 80/443 -> nodeport)
    listen_port      = number
    destination_port = number
    proxyprotocol    = optional(bool, false)
  }))

  default = [
    {
      name             = "http"
      protocol         = "tcp"
      listen_port      = 80
      destination_port = 30080
      proxyprotocol    = false
    },
    {
      name             = "https"
      protocol         = "tcp"
      listen_port      = 443
      destination_port = 30443
      proxyprotocol    = false
    }
  ]
}
