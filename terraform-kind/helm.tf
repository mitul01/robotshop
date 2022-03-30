provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

resource "kubernetes_namespace" "namespace-robot-shop" {
  metadata {
    name = "robot-shop"   
    labels = {
      istio-injection="enabled"
        }
    }
    depends_on = [
      kind_cluster.default
    ]
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
  depends_on = [
    kind_cluster.default,kubernetes_namespace.namespace-robot-shop
  ]
}