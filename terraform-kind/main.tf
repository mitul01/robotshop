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

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

resource "kubernetes_namespace" "minikube-namespace-robot-shop" {
  metadata {
    name = "robot-shop"   
    labels = {
      istio-injection="enabled"
        }
    }
}
resource "helm_release" "robot-shop" {
  name = "robot-shop"
  chart = "../helm/."
  values = [
    "${file("../helm/values.yaml")}"
  ]
  namespace = "robot-shop"
  set {
    name  = "istio.enabled"
    value = "false"
  }
}
