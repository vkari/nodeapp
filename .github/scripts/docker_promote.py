"""Promote Docker image from non-prod ACR to prod ACR via Azure CLI.

The script expects the following environment variables to be set:

AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID - service principal creds
NONPROD_ACR - name of the non-prod ACR
PROD_ACR - name of the prod ACR
IMAGE_PATH - repository path in the registry
DOCKER_TAG - tag of the image to promote

Optional environment variables for AKS context:
NONPROD_RG - non-prod resource group
NONPROD_CLUSTER - non-prod AKS name
PROD_RG - prod resource group
PROD_CLUSTER - prod AKS name

The script logs into Azure, checks if the requested Docker tag already
exists in the production registry and only promotes the image from the
non-prod registry if required.
"""

import os
import subprocess
from typing import List


def run(cmd: List[str]) -> str:
    """Run a command and capture its output."""
    print(f"➡️  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = result.stdout.decode().strip()
    if output:
        print(output)
    return output


def az_login() -> None:
    """Login to Azure using service principal credentials."""
    client_id = os.environ.get("AZURE_CLIENT_ID")
    secret = os.environ.get("AZURE_CLIENT_SECRET")
    tenant = os.environ.get("AZURE_TENANT_ID")
    subscription = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not all([client_id, secret, tenant]):
        raise SystemExit(
            "AZURE_CLIENT_ID, AZURE_CLIENT_SECRET and AZURE_TENANT_ID must be set"
        )

    run([
        "az",
        "login",
        "--service-principal",
        "-u",
        client_id,
        "-p",
        secret,
        "--tenant",
        tenant,
    ])

    if subscription:
        run(["az", "account", "set", "--subscription", subscription])


def set_aks_context(resource_group: str, cluster: str) -> None:
    """Set kubectl context for an AKS cluster."""
    if resource_group and cluster:
        run([
            "az", "aks", "get-credentials",
            "--resource-group", resource_group,
            "--name", cluster,
            "--overwrite-existing",
        ])


def login_acr(acr_name: str) -> None:
    run(["az", "acr", "login", "--name", acr_name])


def tag_exists(acr_name: str, repository: str, tag: str) -> bool:
    """Return True if the tag exists in the specified ACR repository."""
    try:
        output = run(
            [
                "az",
                "acr",
                "repository",
                "show-tags",
                "--name",
                acr_name,
                "--repository",
                repository,
                "--output",
                "tsv",
            ]
        )
    except subprocess.CalledProcessError:
        return False

    return tag in output.split()


def promote_image() -> None:
    nonprod_acr = os.environ.get("NONPROD_ACR")
    prod_acr = os.environ.get("PROD_ACR")
    image_path = os.environ.get("IMAGE_PATH")
    tag = os.environ.get("DOCKER_TAG")

    if not all([nonprod_acr, prod_acr, image_path, tag]):
        raise SystemExit("NONPROD_ACR, PROD_ACR, IMAGE_PATH and DOCKER_TAG must be set")

    src_image = f"{nonprod_acr}.azurecr.io/{image_path}:{tag}"
    dest_image = f"{prod_acr}.azurecr.io/{image_path}:{tag}"

    if tag_exists(prod_acr, image_path, tag):
        print(f"✅ Image {dest_image} already exists. Skipping promotion.")
        return

    print(f"🔄 Promoting {src_image} to {dest_image}")

    login_acr(nonprod_acr)
    run(["docker", "pull", src_image])

    run(["docker", "tag", src_image, dest_image])

    login_acr(prod_acr)
    run(["docker", "push", dest_image])


def main():
    az_login()

    set_aks_context(os.environ.get("NONPROD_RG", ""), os.environ.get("NONPROD_CLUSTER", ""))
    set_aks_context(os.environ.get("PROD_RG", ""), os.environ.get("PROD_CLUSTER", ""))

    promote_image()


if __name__ == "__main__":
    main()
