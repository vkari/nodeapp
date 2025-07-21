#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh

export AZURE_CONFIG_DIR="${GITHUB_WORKSPACE}/.azure"
export REPO_NAME=${GITHUB_REPOSITORY#$GITHUB_REPOSITORY_OWNER/}

echo "[DEBUG] az login"
az_login $AZURE_CLIENT_ID $AZURE_TENANT_ID $AZURE_CLIENT_SECRET

echo "Show list of files in $pwd"
ls -lah || true

echo "Make sure $FILE_PATH is created"
mkdir -p ${GITHUB_WORKSPACE}/$FILE_PATH

echo "Download the file from blob - az storage blob download..."
az storage blob download \
    --account-name $STORAGE_ACCOUNT \
    --container-name $BLOB_CONTAINER \
    --name $FILE_NAME \
    --file "${GITHUB_WORKSPACE}/$FILE_PATH/$FILE_NAME" \
    --auth-mode login

echo "Show the downloaded file in the $FILE_PATH"
ls -lah ${GITHUB_WORKSPACE}/$FILE_PATH || true
