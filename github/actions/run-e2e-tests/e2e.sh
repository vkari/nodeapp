#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh
cp ${GITHUB_ACTION_PATH}/../shared/settings.xml ./settings.xml

if [ -n "$track" ]; then
  track=$(echo $track | sed -e 's/track//')
  e=$(echo $e$track)
fi

for env in $(find ${GITHUB_WORKSPACE}/.github/workflows/helm_vars -maxdepth 1 -mindepth 1 -type d -name "$e*") ; do 
    env=${env%*/}
    env_short=${env##*/}
    replicas_num=$(grep -s "replica" ${GITHUB_WORKSPACE}/.github/workflows/helm_vars/$env_short/values.yaml | sed 's/replica:\ //')

    if [ -z "$replicas_num" ] || [ $replicas_num -eq 0 ]; then
        echo "Skipping e2e tests for $env_short as it's not deployed there"
    else
    cd ${GITHUB_WORKSPACE}/e2e
    echo "Running e2e tests for $env_short environment"
    echo "Command: mvn clean install -Denv=$env_short"
    mvn -s ../settings.xml clean install -Denv=$env_short
    mv allure-results ${GITHUB_WORKSPACE}/allure-results-folder-for-$env_short
    fi
done
