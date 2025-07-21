#!/bin/bash

export AZURE_CLI_DISABLE_CONNECTION_VERIFICATION=1
# Suppress urllib3 InsecureRequestWarning messages triggered by the Azure CLI
export PYTHONWARNINGS="ignore:Unverified HTTPS request"

# Function to handle environment variable name normalization
get_env_var() {
  var_name="$1"
  var_value=$(printenv "$var_name" || printenv "$(echo "$var_name" | tr '-' '_')")

  if [ -z "$var_value" ]; then
    echo "Environment variable $var_name or ${var_name//-/_} not set."
    exit 1
  else
    echo "$var_value"
  fi
}

# Define variables for Azure Key Vault access with normalized env var names
source_kv_url=$(get_env_var "SOURCE_KV_URL")
client_id=$(get_env_var "CLIENT_ID")
client_secret=$(get_env_var "CLIENT_SECRET")
tenant_id=$(get_env_var "TENANT_ID")

# Other variables
app_id=$1
prefix="ecom-$app_id"
suffix=$2
fname="$prefix-$suffix"

if [ -z "$source_kv_url" ] || [ -z "$client_id" ] || [ -z "$client_secret" ] || [ -z "$tenant_id" ]; then
  echo "One or more required environment variables are not set."
  exit 1
fi

vault_name=$(echo "$source_kv_url" | awk -F[/:] '{print $4}' | cut -d'.' -f1)

echo "Using Key Vault URL: $source_kv_url"
echo "Extracted Key Vault name: $vault_name"

export AZURE_CLI_DISABLE_CONNECTION_VERIFICATION=1

az login --service-principal -u "$client_id" -p "$client_secret" --tenant "$tenant_id"
if [ $? -ne 0 ]; then
  echo "Azure login failed!"
  exit 1
fi

VARIABLE_FILE="./variable.txt"

# Check if the variable.txt file exists
if [ ! -f "$VARIABLE_FILE" ]; then
  echo "variable.txt file not found!"
  exit 1
fi

while IFS= read -r key || [ -n "$key" ]; do
  if [ -z "$key" ]; then
    continue
  fi

  echo "Processing key: $key"

  full_key=$(echo "$fname-$key" | xargs | tr '[:lower:]' '[:upper:]' | tr '_' '-')
  env_key=$(echo "$key" | tr '-' '_')

  echo "Retrieving value for key: $full_key"
  value=$(az keyvault secret show --vault-name "$vault_name" --name "$full_key" --query value -o tsv)

  if [ $? -ne 0 ]; then
    echo "Failed to retrieve value for key: $full_key"
  else
    trimmed_key=$(echo "$key" | xargs | tr '[:lower:]' '[:upper:]')
    env_key=$(echo "$trimmed_key" | tr '-' '_')

    if [ -z "$value" ]; then
      echo "Value for $full_key is empty or could not be retrieved."
    else
      export "$env_key"="$value"
      echo "Exported $env_key=$value"
    fi
  fi
done < "$VARIABLE_FILE"

echo "Exported environment variables:"
printenv | grep -E "$(paste -sd '|' $VARIABLE_FILE | tr '-' '_')"

export BUILD_ENV="${suffix}"
echo "BUILD_ENV=$BUILD_ENV"
echo "Key Vault secrets retrieved successfully!"
