locals {
  jenkins_values = {
    controller = {
      additionalPlugins = [
        "ace-editor:1.1",
        "ansicolor",
        "basic-branch-build-strategies:1.3.2",
        "credentials:2.5",
        "git-server:1.10",
        "groovy",
        "junit:1.51",
        "pipeline-model-api:1.8.5",
        "pipeline-model-definition:1.8.5",
        "pipeline-model-extensions:1.8.5",
        "workflow-cps:2.92",
        "workflow-job:2.41",
        "workflow-support:3.8",
      ],
      agentListenerPort = var.jenkins_agent_port
      jenkinsUrl        = "http://localhost:${var.jenkins_ui_port}"
      initScripts       = [file("${path.module}/init.groovy")]
      JCasC = {
        enabled       = true
        defaultConfig = true
        configScripts = {
          jenkins = yamlencode({
            jenkins = {
              systemMessage = "Welcome to Jenkins & Consul & Friends",
              nodes = [{
                permanent = {
                  labelString = "localhost"
                  launcher = {
                    jnlp = {
                      workDirSettings = {
                        disabled : false
                        failIfWorkDirIsMissing : false
                        internalDir : "remoting"
                      }
                    }
                  }
                  name              = "localhost"
                  remoteFS          = "/tmp/jenkins"
                  retentionStrategy = "always"
                }
              }]
            }
          })
        }
      }
      installLatestPlugins          = true
      installLatestSpecifiedPlugins = true
      servicePort                   = var.jenkins_ui_port
    }
    persistence = {
      size = "100M"
    }
  }
}

resource "kubernetes_namespace" "jenkins" {
  metadata {
    name = "jenkins"
  }
}

resource "random_string" "local_pv" {
  length  = 16
  special = false
}

resource "kubernetes_persistent_volume" "local_pv" {
  metadata {
    name = "local-pv"
  }
  spec {
    capacity = {
      storage = "100M"
    }
    access_modes       = ["ReadWriteMany"]
    storage_class_name = "manual"
    persistent_volume_source {
      local {
        path = "/mnt"
      }
    }
    node_affinity {
      required {
        node_selector_term {
          match_expressions {
            key      = "kubernetes.io/hostname"
            operator = "In"
            values   = [var.local_volume_node_hostname]
          }
        }
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "jenkins" {
  metadata {
    name      = "jenkins-local-pvc"
    namespace = kubernetes_namespace.jenkins.id
  }
  spec {
    access_modes       = ["ReadWriteMany"]
    storage_class_name = "manual"
    resources {
      requests = {
        storage = "100M"
      }
    }
    volume_name = kubernetes_persistent_volume.local_pv.metadata.0.name
  }
}

resource "kubernetes_secret" "jenkins" {
  metadata {
    name      = "jenkins-admin"
    namespace = kubernetes_namespace.jenkins.id
  }
  data = {
    "jenkins-admin-user"     = "admin"
    "jenkins-admin-password" = "admin"
  }
}

resource "helm_release" "jenkins" {
  name             = "jenkins"
  chart            = "../../helm/jenkins/charts/jenkins"
  namespace        = kubernetes_namespace.jenkins.id
  force_update     = true
  recreate_pods    = true
  wait             = true
  create_namespace = true
  values           = [data.utils_deep_merge_yaml.jenkins_values.output]
}

data "utils_deep_merge_yaml" "jenkins_values" {
  input = [
    yamlencode(local.jenkins_values),
    yamlencode({
      controller = {
        admin = {
          existingSecret : resource.kubernetes_secret.jenkins.metadata.0.name
        }
      }
      persistence = {
        existingClaim : kubernetes_persistent_volume_claim.jenkins.metadata.0.name
      }
    })
  ]
}
