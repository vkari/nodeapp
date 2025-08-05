#!/usr/bin/env python3
"""Promote a container image from non-prod ACR to prod ACR.

This script mirrors the authentication logic used in the composite
`docker-publish` action. Instead of performing an `az login` and setting
subscriptions, it authenticates directly to each registry using the
provided credentials (falling back to ``az acr login`` when no credentials
are supplied).

It accepts either eight arguments (the simplified interface) or ten
arguments where non-prod and prod subscription IDs are supplied after the
non-prod credentials. The subscription values are ignored, allowing legacy
calls to continue working without modification.

Steps performed:
1. Log in to the non-prod registry and pull the specified image.
2. Retag the image for prod.
3. Log in to the prod registry and push the retagged image.
"""

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


def login_registry(registry, username=None, password=None, name=None):
    """Log in to an ACR registry using docker credentials or `az acr login`."""
    if username and password:
        print(f"🔐 Logging in to {registry} with Docker")
        run(["docker", "login", registry, "-u", username, "-p", password])
    else:
        name = name or registry
        print(f"🔐 Logging in to {name} via az acr")
        run(["az", "acr", "login", "--name", name])


def main(
    nonprod_acr,
    prod_acr,
    image_repo,
    image_tag,
    nonprod_user,
    nonprod_pass,
    prod_user,
    prod_pass,
):
    nonprod_reg = nonprod_acr if "." in nonprod_acr else f"{nonprod_acr}.azurecr.io"
    prod_reg = prod_acr if "." in prod_acr else f"{prod_acr}.azurecr.io"

    # Step 1: log in to non-prod registry and pull image
    login_registry(nonprod_reg, nonprod_user, nonprod_pass, nonprod_acr)
    print(f"📥 Pulling {nonprod_reg}/{image_repo}:{image_tag}")
    run(["docker", "pull", f"{nonprod_reg}/{image_repo}:{image_tag}"])

    # Step 2: retag for prod
    print("🏷️ Retagging for prod")
    run(
        [
            "docker",
            "tag",
            f"{nonprod_reg}/{image_repo}:{image_tag}",
            f"{prod_reg}/{image_repo}:{image_tag}",
        ]
    )

    # Step 3: log in to prod registry and push the image
    login_registry(prod_reg, prod_user, prod_pass, prod_acr)
    print(f"🚀 Pushing to {prod_reg}/{image_repo}:{image_tag}")
    run(["docker", "push", f"{prod_reg}/{image_repo}:{image_tag}"])


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 8:
        main(*args)
    elif len(args) == 10:
        # Legacy calling convention with subscription IDs after the
        # non-prod credentials and after the prod credentials respectively.
        main(args[0], args[1], args[2], args[3], args[4], args[5], args[7], args[8])
    else:
        print(
            "Usage: promote_acr.py <nonprod_acr> <prod_acr> <image_repo> <image_tag> "
            "<nonprod_user> <nonprod_pass> <prod_user> <prod_pass> [<nonprod_subscription> <prod_subscription>]",
        )
        sys.exit(1)
