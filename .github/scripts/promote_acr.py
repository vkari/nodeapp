#!/usr/bin/env python3
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


def ensure_login():
    """Authenticate with a service principal if not already logged in."""
    try:
        subprocess.run(
            ["az", "account", "show", "--output", "none"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return
    except subprocess.CalledProcessError:
        pass

    client_id = os.environ.get("AZURE_CLIENT_ID")
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    if not all([client_id, tenant_id, client_secret]):
        print(
            "Azure CLI not logged in and service principal credentials are missing.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("🔐 Logging in with service principal")
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

    ensure_login()

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

    # Step 5: switch to prod subscription
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
