#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh

export AZURE_CONFIG_DIR="${GITHUB_WORKSPACE}/.azure"
export REPO_NAME=${GITHUB_REPOSITORY#$GITHUB_REPOSITORY_OWNER/}
export registry_np=$AZURE_ACR_NAME_NP.azurecr.io/$REPO_NAME
export kube_context_np=$KUBE_CONTEXT_NP
export rg_np=$RG_NP

if [ -n "$track" ]; then
  track=$(echo $track | sed -e 's/track//')
  e=$(echo $e$track)
fi

env_folder=$(find ${GITHUB_WORKSPACE}/.github/workflows/helm_vars -maxdepth 1 -mindepth 1 -type d -name "$e*")

echo "Checking values for $e environment"

if [ -n "$env_folder" ]; then
    echo "The values for $e environment are available. Proceeding with $e deployment..."
      for env in $env_folder ; do
        env=${env%*/}
        env_short=${env##*/}

        sed -i 's|${version}|'"0.1.0"'|g' ${GITHUB_ACTION_PATH}/helm-package/Chart.yaml
        sed -i 's|${appName}|'"${REPO_NAME}"'|g' ${GITHUB_ACTION_PATH}/helm-package/Chart.yaml
        sed -i 's|${registry}|'"${registry_np}"'|g' ${GITHUB_WORKSPACE}/.github/workflows/helm_vars/$env_short/values.yaml
        sed -i 's|${tag}|'"${ver}"'|g' ${GITHUB_WORKSPACE}/.github/workflows/helm_vars/$env_short/values.yaml

        echo "[DEBUG] az login to non-prod"
        az_login $AZURE_CLIENT_ID $AZURE_TENANT_ID $AZURE_CLIENT_SECRET

        echo "Switch to the k8s context"
        az aks get-credentials --resource-group $rg_np --name $kube_context_np --overwrite-existing
        kubelogin convert-kubeconfig -l azurecli

        echo "Deploying on $env_short"
        helm upgrade --install --kube-context=$kube_context_np $REPO_NAME -n ecom-svc-$env_short ${GITHUB_ACTION_PATH}/helm-package/ -f ${GITHUB_WORKSPACE}/.github/workflows/helm_vars/$env_short/values.yaml --wait --timeout 20m
      done
    
else    
    echo "There're no values for $e environment. Cancelling the job..."
    exit 1
fi
