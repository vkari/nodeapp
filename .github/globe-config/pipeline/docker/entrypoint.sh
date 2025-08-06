#!/bin/bash

source /app/scripts/utilities.sh

if [[ "${NEXT_POD_TYPE}" = "auth" ]]; then

echo "Retrieve AEM variables from vault for NextJS Auth"
export NEXT_CLIENT_ID=$(getParameter "NEXT_CLIENT_ID" "${VAULT_URL}/${TENANT}/react-${ENVIRONMENT}/${NEXT_POD_TYPE}/NEXT_CLIENT_ID")
export NEXT_CLIENT_SECRET=$(getParameter "NEXT_CLIENT_SECRET" "${VAULT_URL}/${TENANT}/react-${ENVIRONMENT}/${NEXT_POD_TYPE}/NEXT_CLIENT_SECRET")
export NEXT_ORG_ID=$(getParameter "NEXT_ORG_ID" "${VAULT_URL}/${TENANT}/react-${ENVIRONMENT}/${NEXT_POD_TYPE}/NEXT_ORG_ID")
export NEXT_META_SCOPES=$(getParameter "NEXT_META_SCOPES" "${VAULT_URL}/${TENANT}/react-${ENVIRONMENT}/${NEXT_POD_TYPE}/NEXT_META_SCOPES")
export NEXT_PRIVATE_KEY=$(getParameter "NEXT_PRIVATE_KEY" "${VAULT_URL}/${TENANT}/react-${ENVIRONMENT}/${NEXT_POD_TYPE}/NEXT_PRIVATE_KEY")
export NEXT_TECHNICAL_ACCOUNT_ID=$(getParameter "NEXT_TECHNICAL_ACCOUNT_ID" "${VAULT_URL}/${TENANT}/react-${ENVIRONMENT}/${NEXT_POD_TYPE}/NEXT_TECHNICAL_ACCOUNT_ID")

else
    echo "Vault variables only needed for AUTH env"
fi

echo "Start NPM"
npm start


