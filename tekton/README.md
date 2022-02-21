Running tekton pipeline for different services using tekton CLI 
```
tkn pipeline start build-deploy-canary \
     --param SERVICE_NAME=cart \
     --param SERVICE_VERSION=v1.1 \
     --param IMAGE_REPOSITORY=docker.io/mitultan \
     --workspace name=build-deploy-workspace,claimName=ci-cd-workspace
```
