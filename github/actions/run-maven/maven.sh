#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh
cp ${GITHUB_ACTION_PATH}/../shared/settings.xml ./settings.xml

export AZURE_CONFIG_DIR="${GITHUB_WORKSPACE}/.azure"
export REPO_NAME=${GITHUB_REPOSITORY#$GITHUB_REPOSITORY_OWNER/}

echo "[DEBUG] az login to non-prod"
az_login $AZURE_CLIENT_ID $AZURE_TENANT_ID $AZURE_CLIENT_SECRET

# login to ACR
az acr login --name $AZURE_ACR_NAME

# build jar
mvn -s settings.xml -U -e -Dsurefire.useFile=false -Dmaven.wagon.http.ssl.insecure=true -Dmaven.wagon.http.ssl.allowall=true clean install package -Dmaven.wagon.http.ssl.insecure=true -Dmaven.wagon.http.ssl.allowall=true -V

# build Docker image and push to ACR
cp ${GITHUB_ACTION_PATH}/okta-com-chain.pem ./okta-com-chain.pem

# add jar file to docker image
number_of_jars=$(ls -1 ./target/ | grep 'jar$' | wc -l | sed -e 's/^[ \t]*//')
if [ $number_of_jars == "1" ]; then
    cp ./target/*.jar ./application.jar
else
    echo "There're more than one target jar files. Please check the build logs..."
    exit 1
fi

docker build -t $AZURE_ACR_NAME.azurecr.io/$REPO_NAME:$ver -f ${GITHUB_ACTION_PATH}/$DOCKERFILE .
docker push $AZURE_ACR_NAME.azurecr.io/$REPO_NAME:$ver
