provider "kubernetes" {
  config_path = var.path_to_kubernetes_config
}

provider "helm" {
  kubernetes {
    config_path = var.path_to_kubernetes_config
  }
}
