#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh

export AZURE_CONFIG_DIR="${GITHUB_WORKSPACE}/.azure"
export REPO_NAME=${GITHUB_REPOSITORY#$GITHUB_REPOSITORY_OWNER/}

#echo "az login to non-prod"
#az_login $AZURE_CLIENT_ID $AZURE_TENANT_ID $AZURE_CLIENT_SECRET

#echo "Login to $AZURE_ACR_NAME ACR"
#az acr login --name $AZURE_ACR_NAME

echo "[DEBUG] docker login $AZURE_ACR_NAME ACR"
docker login $AZURE_ACR_NAME.azurecr.io --username $AZURE_CLIENT_ID --password $AZURE_CLIENT_SECRET

echo "[DEBUG] pwd and list of file in curr dir"
pwd && ls -lah

dockerfiles=$(find ${GITHUB_ACTION_PATH} -maxdepth 1 -mindepth 1 -type f -name "Dockerfile*" | sed 's/\/.*\/.*\/.*\/.*\/.*\/.*\/.*\/.*\/.*\/Dockerfile-//')

for dockerfile in $dockerfiles; do
    rm -rf build-temp || true
    echo "[DEBUG] change dir to the build-temp"
    mkdir -p build-temp
    cp ${GITHUB_ACTION_PATH}/Dockerfile-$dockerfile build-temp/Dockerfile
    cd build-temp

    echo "[DEBUG] docker build $AZURE_ACR_NAME.azurecr.io/$REPO_NAME/gha-runner-$dockerfile:latest"
    docker build -t $AZURE_ACR_NAME.azurecr.io/$REPO_NAME/gha-runner-$dockerfile:latest .

    echo "[DEBUG] docker push $AZURE_ACR_NAME.azurecr.io/$REPO_NAME/gha-runner-$dockerfile:latest"
    docker push $AZURE_ACR_NAME.azurecr.io/$REPO_NAME/gha-runner-$dockerfile:latest
done
