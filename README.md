# robotshop
Robot Shop microservice app with CI/CD piepline

# Steps to follow
1) Create a auth folder to store all the secrets
```
mkdir auth
```
Create secret yaml files in the subdir and add this subdir in your gitignore to protect it from begin available at github repo
```
apiVersion: v1
kind: Secret
metadata:
  name: dockerhub-pass
  annotations:
    tekton.dev/docker-0: https://index.docker.io/v1/
type: kubernetes.io/basic-auth
stringData:
    username: <DOCKER_USERNAME>
    password: <DOCKER_PASSWORD>
---
apiVersion: v1
kind: Secret
metadata:
  name: github-pass
  annotations:
    tekton.dev/git-0: https://github.com
type: kubernetes.io/basic-auth
stringData:
  username: <GIT_USERNAME>
  password: <GIT_PERSONAL_ACCESS TOKEN WITH REPO RIGHTS> 
---
apiVersion: v1
kind: Secret
metadata:
  name: github-pass-argocd
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  url: <REPO_URL>
  password: <GIT_PERSONAL_ACCESS TOKEN WITH REPO RIGHTS> 
  username: <GIT_USERNAME>
---
apiVersion: v1
kind: Secret
metadata:
  name: proxy-secret
stringData:
  url: <WAVEFRONT_URL>
  token: <WAVEFRONT_API_TOKEN>
```
2) Follow along the intialize cluster script to start your cluster
```
.\intialize-cluster.ps1
```
3) Build the CI and CD pipeline using ci-cd-pipeline bash script
```
.\ci-cd-pipeline.ps1
```
4) Access the dashboards for Tekton and Argocd 
```
# Get password for argocd
$pass = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($pass))

kubectl port-forward svc/argocd-server -n argocd 8081:443
# dashboard at -> localhost:8081
```
```
 kubectl --namespace tekton-pipelines port-forward svc/tekton-dashboard 9097:9097
 # dashboard at -> localhost:9097
```
5) Run the tekton pipeline either using pipeline-run.yaml or using tekton cli for different services using parameters
```
tkn pipeline start build-deploy-canary \
     --param SERVICE_NAME=cart \
     --param SERVICE_VERSION=v1.1 \
     --param IMAGE_REPOSITORY=docker.io/mitultan \
     --workspace name=build-deploy-workspace,claimName=ci-cd-workspace
     --serviceaccount=build-bot
```
