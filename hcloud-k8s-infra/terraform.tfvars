# hcloud_token = ""

ip_cidr = "0.0.0.0/0"

admin_cidrs = [ "0.0.0.0/0" ]

firewall_name = "k8s-firewall"

network_cidr = "10.0.0.0/16"

firewall_rules_base = [

  ############################
  # Acesso administrativo
  ############################
  {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0"] # SSH
  },

  ############################
  # Kubernetes API (kubeadm)
  ############################
  {
    direction  = "in"
    protocol   = "tcp"
    port       = "6443"
    source_ips = ["0.0.0.0/0"] # kubectl / admin
  },

  ############################
  # Traefik via Hetzner LB
  ############################
  {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0"] # HTTP público
  },
  {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0"] # HTTPS público
  },

  ############################
  # etcd (privado)
  ############################
  {
    direction  = "in"
    protocol   = "tcp"
    port       = "2379-2380"
    source_ips = ["10.0.0.0/16"]
  },

  ############################
  # kubelet (privado)
  ############################
  {
    direction  = "in"
    protocol   = "tcp"
    port       = "10250"
    source_ips = ["10.0.0.0/16"]
  },

  ############################
  # controller / scheduler
  ############################
  {
    direction  = "in"
    protocol   = "tcp"
    port       = "10257"
    source_ips = ["10.0.0.0/16"]
  },
  {
    direction  = "in"
    protocol   = "tcp"
    port       = "10259"
    source_ips = ["10.0.0.0/16"]
  },

  ############################
  # Flannel VXLAN
  ############################
  {
    direction  = "in"
    protocol   = "udp"
    port       = "8472"
    source_ips = ["10.0.0.0/16"]
  },
  # NodePort — vindo do LB
  { 
    direction="in" 
    protocol="tcp" 
    port="30080" 
    source_ips=["0.0.0.0/0"]
  },
  { 
    direction="in" 
    protocol="tcp" 
    port="30443" 
    source_ips=["0.0.0.0/0"]
  },
  {
  direction  = "in"
  protocol   = "tcp"
  port       = "30000-32767"
  source_ips = ["0.0.0.0/0"]
  },
  ############################
  # Saída liberada
  ############################
  {
    direction       = "out"
    protocol        = "tcp"
    port            = "1-65535"
    destination_ips = ["0.0.0.0/0"]
  },
  {
    direction       = "out"
    protocol        = "udp"
    port            = "1-65535"
    destination_ips = ["0.0.0.0/0"]
  },
  {
    direction       = "out"
    protocol        = "icmp"
    port            = ""
    destination_ips = ["0.0.0.0/0"]
  },
]

allow_nodeport = true


