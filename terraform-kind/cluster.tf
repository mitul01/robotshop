provider "kind" {
}

resource "kind_cluster" "default" {
  name = "new-cluster"
  wait_for_ready = true
  kind_config {
    kind = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"
       extra_port_mappings {
        container_port = 80
        host_port      = 80
      }
      extra_port_mappings {
        container_port = 443
        host_port      = 443
      }
      # extra_port_mappings {
      #   container_port = 8080
      #   host_port      = 30000
      # }
    }

    node {
      role = "worker"
      image = "kindest/node:v1.19.1"
    }
  }
}
provider "kubernetes" {
  config_path = "~/.kube/config"
}