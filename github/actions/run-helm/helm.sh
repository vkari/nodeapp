#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh

export AZURE_CONFIG_DIR="${GITHUB_WORKSPACE}/.azure"
export REPO_NAME=${GITHUB_REPOSITORY#$GITHUB_REPOSITORY_OWNER/}
export registry_np=$AZURE_ACR_NAME_NP.azurecr.io/$REPO_NAME
export registry_p=$AZURE_ACR_NAME_P.azurecr.io/$REPO_NAME
export kube_context_np=$KUBE_CONTEXT_NP
export kube_context_p=$KUBE_CONTEXT_P
export rg_np=$RG_NP
export rg_p=$RG_P

non_prod_env_folders=$(find ${GITHUB_WORKSPACE}/.github/workflows/helm_vars -maxdepth 1 -mindepth 1 -type d -name "$e[1234567890]*")
prod_env_folders=$(find ${GITHUB_WORKSPACE}/.github/workflows/helm_vars -maxdepth 1 -mindepth 1 -type d -name "$e[ab]*")

echo "Checking values for $e environment"

if [ -n "$non_prod_env_folders" ]; then
    echo "The values for $e environment(s) are available. Proceeding with non-prod deployment..."

    for env in $non_prod_env_folders ; do 
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

elif [ -n "$prod_env_folders" ]; then
    echo "The values for $e environment(s) are available. Proceeding with prod deployment..."
    
    for env in $prod_env_folders ; do 
        env=${env%*/}
        env_short=${env##*/}

        sed -i 's|${version}|'"0.1.0"'|g' ${GITHUB_ACTION_PATH}/helm-package/Chart.yaml
        sed -i 's|${appName}|'"${REPO_NAME}"'|g' ${GITHUB_ACTION_PATH}/helm-package/Chart.yaml
        sed -i 's|${registry}|'"${registry_p}"'|g' ${GITHUB_WORKSPACE}/.github/workflows/helm_vars/$env_short/values.yaml
        sed -i 's|${tag}|'"${ver}"'|g' ${GITHUB_WORKSPACE}/.github/workflows/helm_vars/$env_short/values.yaml

        echo "[DEBUG] az login to non-prod"
        az_login $AZURE_CLIENT_ID $AZURE_TENANT_ID $AZURE_CLIENT_SECRET
        
        echo "Pull and tag the release image $ver from non-prod ACR"
        az acr login --name $AZURE_ACR_NAME_NP
        docker pull $registry_np:$ver
        docker tag $registry_np:$ver $registry_p:$ver

        echo "[DEBUG] az login to prod"
        az_login $AZURE_CLIENT_ID_PROD $AZURE_TENANT_ID_PROD $AZURE_CLIENT_SECRET_PROD

        echo "Push release image $ver to prod ACR"
        az acr login --name $AZURE_ACR_NAME_P
        docker push $registry_p:$ver

        echo "Switch to the k8s context"
        az aks get-credentials --resource-group $rg_p --name $kube_context_p --overwrite-existing
        kubelogin convert-kubeconfig -l azurecli

        echo "Deploying on $env_short"
        helm upgrade --install --kube-context=$kube_context_p $REPO_NAME -n ecom-svc-$env_short ${GITHUB_ACTION_PATH}/helm-package/ -f ${GITHUB_WORKSPACE}/.github/workflows/helm_vars/$env_short/values.yaml --wait --timeout 20m
    done
    
else    
    echo "There're no values for $e environment(s). Cancelling the job..."
    exit 1
fi
