Running tekton pipeline for different services using tekton CLI 
```
tkn pipeline start build-deploy-canary \
     --param SERVICE_NAME=cart \
     --param SERVICE_VERSION=v1.1 \
     --workspace name=build-deploy-workspace,claimName=ci-cd-workspace
```
