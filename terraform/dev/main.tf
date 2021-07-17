module "jenkins" {
  source = "../modules/jenkins"

  jenkins_agent_port         = var.jenkins_agent_port
  jenkins_ui_port            = var.jenkins_ui_port
  local_volume_node_hostname = var.local_volume_node_hostname
}

module "consul" {
  source = "../modules/consul"

  consul_ui_port  = var.consul_ui_port
  consul_dns_port = var.consul_dns_port
}
