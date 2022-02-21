echo "Building Tekton Resources"
kubectl apply -f tekton/.

echo "Building Argocd Resources"
kubectl apply -f argocd/application.yaml
