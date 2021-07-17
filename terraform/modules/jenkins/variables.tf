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