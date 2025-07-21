#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh

export AZURE_CONFIG_DIR="${GITHUB_WORKSPACE}/.azure"
export REPO_NAME=${GITHUB_REPOSITORY#$GITHUB_REPOSITORY_OWNER/}
export KUBECONFIG=/root/.kube/config

if [ $E == "prod" ]; then
    echo "[DEBUG] set prod centralus for RG and AKS"
    export kube_context_p=$KUBE_CONTEXT_P_CENTRAL
    export rg_p=$RG_P_CENTRAL
elif [ $E == "proda" ] || [ $E == "prodb" ]; then
    echo "[DEBUG] set prod eastus for RG and AKS"
    export kube_context_p=$KUBE_CONTEXT_P
    export rg_p=$RG_P
else
    echo "[DEBUG] set non-prod eastus for RG and AKS"
    export kube_context_np=$KUBE_CONTEXT_NP
    export rg_np=$RG_NP
fi

if [[ $E != *"prod"* ]]; then
    echo "[DEBUG] az login to non-prod"
    az_login $AZURE_CLIENT_ID $AZURE_TENANT_ID $AZURE_CLIENT_SECRET

    echo "[DEBUG] az aks get-credentials for non-prod aks"
    az aks get-credentials --resource-group $rg_np --name $kube_context_np --overwrite-existing
    kubelogin convert-kubeconfig -l azurecli

    echo "[DEBUG] helm rollback"
    helm rollback --kube-context=$kube_context_np $SERVICE -n ecom-svc-$E --wait --timeout 20m

elif [[ $E == *"prod"* ]]; then
    echo "[DEBUG] az login to prod"
    az_login $AZURE_CLIENT_ID_PROD $AZURE_TENANT_ID_PROD $AZURE_CLIENT_SECRET_PROD

    echo "[DEBUG] az aks get-credentials for prod aks"
    az aks get-credentials --resource-group $rg_p --name $kube_context_p --overwrite-existing
    kubelogin convert-kubeconfig -l azurecli
        
    echo "[DEBUG] helm rollback"
    helm rollback --kube-context=$kube_context_p $SERVICE -n ecom-svc-$E --wait --timeout 20m
fi
