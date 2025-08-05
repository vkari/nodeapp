#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys


def run(cmd):
    """Run a command and return its stdout, surfacing all output on failure."""
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
        # Surface CLI errors for easier debugging
        print("Command failed:", " ".join(cmd), file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        raise


def main(
    nonprod_acr,
    prod_acr,
    image_repo,
    image_tag,
    nonprod_user,
    nonprod_pass,
    prod_user,
    prod_pass,
    prod_subscription,
):
    if not shutil.which("az"):
        print("Azure CLI not found. Please install az before running this script.")
        sys.exit(1)

    # Ensure the CLI is authenticated; fall back to service principal login if needed
    try:
        subprocess.run(
            ["az", "account", "show", "--output", "none"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError:
        client_id = os.environ.get("AZURE_CLIENT_ID")
        tenant_id = os.environ.get("AZURE_TENANT_ID")
        client_secret = os.environ.get("AZURE_CLIENT_SECRET")

        if not all([client_id, tenant_id, client_secret]):
            print(
                "Azure CLI not logged in and service principal credentials are missing.",
                file=sys.stderr,
            )
            sys.exit(1)

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


    run(["az", "account", "set", "--subscription", prod_subscription])
    
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID_PROD") or os.environ.get(
        "AZURE_SUBSCRIPTION_ID"
    )
    if subscription_id:
        run(["az", "account", "set", "--subscription", subscription_id])

    nonprod_login = nonprod_acr if '.' in nonprod_acr else f"{nonprod_acr}.azurecr.io"

    # Check if tag exists in prod registry
    try:
        tags_output = run([
            "az",
            "acr",
            "repository",
            "show-tags",
            "--name",
            prod_acr,
            "--repository",
            image_repo,
            "--output",
            "tsv",
            "--username",
            prod_user,
            "--password",
            prod_pass,
            "--subscription",
            prod_subscription,
        ])
        if image_tag in tags_output.splitlines():
            print(f"Image {image_repo}:{image_tag} already exists in {prod_acr}")
            return
    except subprocess.CalledProcessError:
        # Repository may not exist yet; proceed with import
        pass

    print(f"Promoting {image_repo}:{image_tag} from {nonprod_acr} to {prod_acr}")

    # Authenticate to the target registry so the import command can push the image
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
            "--subscription",
            prod_subscription,
        ]
    )

    # Import the image into prod
    run(
        [
            "az",
            "acr",
            "import",
            "--name",
            prod_acr,
            "--source",
            f"{nonprod_login}/{image_repo}:{image_tag}",
            "--image",
            f"{image_repo}:{image_tag}",
            "--username",
            nonprod_user,
            "--password",
            nonprod_pass,
            "--subscription",
            prod_subscription,
        ]
    )


if __name__ == "__main__":
    if len(sys.argv) != 10:
        print(
            "Usage: promote_acr.py <nonprod_acr> <prod_acr> <image_repo> <image_tag> "
            "<nonprod_user> <nonprod_pass> <prod_user> <prod_pass> <prod_subscription>",
        )
        sys.exit(1)
    main(*sys.argv[1:])
