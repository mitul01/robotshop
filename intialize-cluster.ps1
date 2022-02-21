# Create Secrets 
echo "Creating essential credentials"
kubectl apply -f auth/.

# Deploying the wavefront proxy
echo "Deploying Wavefront proxy"
kubectl apply -f wavefront/wavefront-proxy.yaml

# Create a Jaeger operator
echo "Creating a Jaeger operator...."
kubectl create namespace observability 
kubectl create -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.30.0/jaeger-operator.yaml -n observability

# Build the Argo agent
echo "Building the Argo agent for CD operations....."
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# wait for some time to free up resources
start-sleep -Seconds 300

echo "Tekton operator"
kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

echo "Tekton dashboard"
kubectl apply --filename https://github.com/tektoncd/dashboard/releases/latest/download/tekton-dashboard-release.yaml

echo "tekton-triggers"
kubectl apply --filename https://storage.googleapis.com/tekton-releases/triggers/latest/release.yaml
kubectl apply --filename https://storage.googleapis.com/tekton-releases/triggers/latest/interceptors.yaml 

echo "Cluster Intialized :)"
