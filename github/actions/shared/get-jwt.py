#!/usr/bin/env python3
import jwt
import os
import requests
import time

# Open PEM
signing_key = jwt.jwk_from_pem(os.environ['GITHUB_APP_PRIVATE_KEY'].encode('utf-8'))

payload = {
    # Issued at time
    'iat': int(time.time()),
    # JWT expiration time (10 minutes maximum)
    'exp': int(time.time()) + 600,
    # GitHub App's identifier
    'iss': os.environ['GITHUB_APP_ID']
}

jwt_instance = jwt.JWT()
encoded_jwt = jwt_instance.encode(payload, signing_key, alg='RS256')

response = requests.post(
    f"{os.environ['GITHUB_API_URL']}/app/installations/{os.environ['GITHUB_APP_INSTALLATION_ID']}/access_tokens",
    headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {encoded_jwt}",
    },
    timeout=60
)

print(f'token={response.json()["token"]}')
