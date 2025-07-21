##

function getParameter() {
  if [ $# -gt 2 ] || [ $# -lt 1 ]; then
    echo "Error"
  else
    if [ $# == 2 ]; then
      remotPara=$(curl -m 60 -s -X GET -H "X-Vault-Token:$VAULT_TOKEN" "${2}" | jq -r .data.value)
      if [ "$remotPara" != "null" ] && [ "$remotPara" != "" ]; then
        echo $remotPara
      else
        if [ -n "${!1}" ]; then
          echo ${!1}
        else
          echo "null"
        fi
      fi
    else
      if [ -n "${!1}" ]; then
        echo ${!1}
      else
        echo "null"
      fi
    fi
  fi
}
