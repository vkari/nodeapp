#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh

export AZURE_CONFIG_DIR="${GITHUB_WORKSPACE}/.azure"
export REPO_NAME=${GITHUB_REPOSITORY#$GITHUB_REPOSITORY_OWNER/}

echo "[DEBUG] az login"
az_login $AZURE_CLIENT_ID $AZURE_TENANT_ID $AZURE_CLIENT_SECRET

# login to ACR
echo "Login to $AZURE_ACR_NAME ACR repository"
az acr login --name $AZURE_ACR_NAME
echo "List repositories in the $AZURE_ACR_NAME"
az acr repository list -n $AZURE_ACR_NAME || true

# fix version for release branches with reserved minor versions from 80 to 99
echo "original branch name $BRANCH_NAME"
BRANCH_NAME_NEW=$(echo $BRANCH_NAME | sed -e 's/.[8-9][0-9]$/.00/')
echo "updated branch name $BRANCH_NAME_NEW"

echo "Checking if ACR repository $REPO_NAME exists"
IF_REPO_NAME=$(az acr repository list -n $AZURE_ACR_NAME | grep "$REPO_NAME" | sed -e 's/  "//' | sed -e 's/",//' || true)
echo "$IF_REPO_NAME"

# check if the acr repository exists
if [ -z "$IF_REPO_NAME" ]; then
    # trigger new version creation for the new acr repository
    echo "ACR repository $REPO_NAME doesn't exist. Let's set up the new version and push the first image..."
    CURR_VER=""
else
    echo "ACR repository $REPO_NAME exists; continue with the next steps..."
    # get the current version
    echo "Getting the current tag"
    CURR_VER=$(az acr repository show-tags -n $AZURE_ACR_NAME --repository $REPO_NAME --orderby time_desc | jq -r --arg branch "$BRANCH_NAME_NEW" 'first(.[] | select (. | startswith($branch)))')
    echo "latest version for branch $BRANCH_NAME_NEW is $CURR_VER"
fi

if [[ $CURR_VER == "ERROR"* ]] || [ -z "$CURR_VER" ]; then
    echo "ver=$BRANCH_NAME_NEW.1" >> $GITHUB_OUTPUT
else
    BUILD_CURR_VER=$(echo $CURR_VER | rev | cut -d '.' -f 1 | rev)
    BUILD_VER=$((BUILD_CURR_VER + 1))
    echo "ver=$BRANCH_NAME_NEW.$BUILD_VER" >> $GITHUB_OUTPUT
fi
