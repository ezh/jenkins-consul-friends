variable "path_to_kubernetes_config" {
  type = string
}

variable "jenkins_ui_port" {
  type    = number
  default = 8080
}

variable "jenkins_agent_port" {
  type    = number
  default = 50000
}

variable "local_volume_node_hostname" {
  type = string
}

variable "consul_ui_port" {
  type    = number
  default = 8500
}

variable "consul_dns_port" {
  type    = number
  default = 8600
}
