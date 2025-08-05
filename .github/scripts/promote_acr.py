#!/usr/bin/env python3
"""Promote a container image from non-prod ACR to prod ACR.

Steps performed:
1. Log in using the non-prod service principal (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET,
   AZURE_TENANT_ID).
2. Select the non-prod subscription and pull the image from the non-prod registry.
3. Retag the image for prod.
4. Log in using the prod service principal (AZURE_CLIENT_ID_PROD,
   AZURE_CLIENT_SECRET_PROD, AZURE_TENANT_ID_PROD).
5. Select the prod subscription and push the image to the prod registry.
"""

import os
import shutil
import subprocess
import sys


def run(cmd):
    """Run a shell command, showing output when it fails."""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print("Command failed:", " ".join(cmd), file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        raise


def login_service_principal(client_id, client_secret, tenant_id):
    """Authenticate with a specific service principal."""
    if not all([client_id, client_secret, tenant_id]):
        print("Missing service principal credentials", file=sys.stderr)
        sys.exit(1)

    print(f"🔐 Logging in with service principal {client_id}")
    run(
        [
            "az",
            "login",
            "--service-principal",
            "-u",
            client_id,
            "-p",
            client_secret,
            "--tenant",
            tenant_id,
        ]
    )


def main(
    nonprod_acr,
    prod_acr,
    image_repo,
    image_tag,
    nonprod_user,
    nonprod_pass,
    prod_user,
    prod_pass,
    nonprod_subscription,
    prod_subscription,
):
    if not shutil.which("az"):
        print("Azure CLI not found. Please install az before running this script.")
        sys.exit(1)

    # Step 1: authenticate to non-prod
    login_service_principal(
        os.environ.get("AZURE_CLIENT_ID"),
        os.environ.get("AZURE_CLIENT_SECRET"),
        os.environ.get("AZURE_TENANT_ID"),
    )

    nonprod_reg = nonprod_acr if "." in nonprod_acr else f"{nonprod_acr}.azurecr.io"
    prod_reg = prod_acr if "." in prod_acr else f"{prod_acr}.azurecr.io"

    # Step 2: select non-prod subscription
    print(f"🔧 Selecting non-prod subscription {nonprod_subscription}")
    run(["az", "account", "set", "--subscription", nonprod_subscription])

    # Step 3: log in to non-prod registry and pull image
    print(f"📥 Pulling {nonprod_reg}/{image_repo}:{image_tag}")
    run(
        [
            "az",
            "acr",
            "login",
            "--name",
            nonprod_acr,
            "--username",
            nonprod_user,
            "--password",
            nonprod_pass,
        ]
    )
    run(["docker", "pull", f"{nonprod_reg}/{image_repo}:{image_tag}"])

    # Step 4: retag for prod
    print("🏷️ Retagging for prod")
    run(
        [
            "docker",
            "tag",
            f"{nonprod_reg}/{image_repo}:{image_tag}",
            f"{prod_reg}/{image_repo}:{image_tag}",
        ]
    )

    # Step 5: authenticate and switch to prod
    login_service_principal(
        os.environ.get("AZURE_CLIENT_ID_PROD"),
        os.environ.get("AZURE_CLIENT_SECRET_PROD"),
        os.environ.get("AZURE_TENANT_ID_PROD"),
    )
    print(f"🔧 Selecting prod subscription {prod_subscription}")
    run(["az", "account", "set", "--subscription", prod_subscription])

    # Step 6: log in to prod registry and push the image
    print(f"🚀 Pushing to {prod_reg}/{image_repo}:{image_tag}")
    run(
        [
            "az",
            "acr",
            "login",
            "--name",
            prod_acr,
            "--username",
            prod_user,
            "--password",
            prod_pass,
        ]
    )
    run(["docker", "push", f"{prod_reg}/{image_repo}:{image_tag}"])


if __name__ == "__main__":
    if len(sys.argv) != 11:
        print(
            "Usage: promote_acr.py <nonprod_acr> <prod_acr> <image_repo> <image_tag> "
            "<nonprod_user> <nonprod_pass> <prod_user> <prod_pass> "
            "<nonprod_subscription> <prod_subscription>",
        )
        sys.exit(1)
    main(*sys.argv[1:])
