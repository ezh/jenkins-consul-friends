resource "docker_image" "consul" {
  name         = "consul:1.9.7"
  keep_locally = true
}

resource "docker_network" "private_network" {
  name = "jenkins-consul-friends"
}

resource "docker_container" "consul_server" {
  command = [
    "agent", "-server", "-bootstrap-expect", "1", "-ui",
    "-retry-interval", "5s", "-client", "0.0.0.0"
  ]
  hostname = "jenkins_consul_friends_consul_server"
  image    = docker_image.consul.latest
  name     = "jenkins_consul_friends_consul_server"
  restart  = "always"
  networks_advanced {
    name = docker_network.private_network.name
  }
  ports {
    internal = 8500
    external = var.consul_ui_port
  }
  ports {
    internal = 8600
    external = var.consul_dns_port
    protocol = "udp"
  }
}

resource "docker_container" "consul_client" {
  command = [
    "agent", "-retry-join", "jenkins_consul_friends_consul_server",
    "-retry-interval", "5s", "-client", "0.0.0.0"
  ]
  hostname = "jenkins_consul_friends_consul_client"
  image    = docker_image.consul.latest
  name     = "jenkins_consul_friends_consul_client"
  restart  = "always"
  networks_advanced {
    name = docker_network.private_network.name
  }
}
