// get below config using kubectl config view 
  // server -> host 
  // certificate-authority -> cluster_ca_certificate
  // client-certificate -> client_certificate
  // client-key -> client_key
provider "kubernetes" {
  host = "https://172.21.66.118:8443"
  client_certificate     = file("C:/Users/mtandon/.minikube/profiles/minikube/client.crt")
  client_key             = file("C:/Users/mtandon/.minikube/profiles/minikube/client.key")
  cluster_ca_certificate = file("C:/Users/mtandon/.minikube/ca.crt")
}
 provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

resource "kubernetes_namespace" "minikube-namespace" {
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
}