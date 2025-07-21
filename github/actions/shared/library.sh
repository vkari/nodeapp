#!/bin/bash

# Azure Login for Non-Prod Subscription(s)
az_login() {
    max_attempts=10;
    attempt=1;
    success=false;
    while [[ $attempt -le $max_attempts && $success != true ]]; do
        #if output=$(az login --service-principal -u ${AZURE_CLIENT_ID} -t ${AZURE_TENANT_ID} --federated-token $(cat ${AZURE_FEDERATED_TOKEN_FILE}) 2>&1); then
        if output=$(az login --service-principal -u $1 -t $2 --password $3); then
            echo "[INFO] Success";
            echo $output;
            success=true;
        else
            if [[ $output != *"reason: Forbidden"* ]]; then
                echo "[ERROR] Error: $output";
                exit 1;
            fi;
        fi;

        echo "[DEBUG] Attempt: $attempt, Max Attempts: $max_attempts, Success: $success"

        if [[ $attempt -eq $max_attempts ]]; then
            echo "[ERROR] Error: $output";
        fi

        if [[ $attempt -ne $max_attempts && $success != true ]]; then
            sleep 10
        fi

        ((attempt++));

    done
}

uses() {
    [ ! -z "${1}" ]
}

check_inputs() {
    if [ -z "${!1}" ]; then
        echo "[ERROR] The "${1}" value is null";
        exit 1;
    fi
}

# get_old_blobs function
get_old_blobs() {

  # Get the current date and time
  currentDate=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  # Func Input Variables
  storageAccount="$1"
  containerName="$2"
  prefix="$3"
  dayRange="$4"

  # Get the list of blobs
  blobs=$(az storage blob list --account-name "$storageAccount" --auth-mode login --container-name "$containerName" --prefix "$prefix" --query "[].{name:name, lastModified:properties.lastModified}")

  # Convert the JSON output to lines
  blobs=$(echo $blobs | jq -r '.[] | "\(.lastModified) \(.name)"')

  # Filter the blobs based on the last modified date
  oldBlobs=$(echo "$blobs" | while read -r blob; do
    lastModified=$(echo "$blob" | cut -d' ' -f1)
    name=$(echo "$blob" | cut -d' ' -f2-)

    # Calculate the difference in days
    diff=$(($(($(date -u -d "$currentDate" +%s) - $(date -u -d "$lastModified" +%s))) / 60 / 60 / 24))

    if (( diff >= dayRange)); then
      echo "$name"
    fi
  done)
  
  if [ -z "$oldBlobs" ]; then
    echo "No files found or qualify for operation."
  else
    echo "$oldBlobs"
  fi
}