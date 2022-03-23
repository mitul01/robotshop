kubectl create ns robot-shop
kubectl label namespace robot-shop istio-injection=enabled
kubectl install -f /istio-addons/.
helm install robot-shop --namespace robot-shop ../helm/.

# Access kiali dashboard using port-forwarding 
kubectl port-forward svc/kiali -n istio-system 20001