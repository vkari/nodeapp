#!/usr/bin/env python3
import subprocess
import sys


def run(cmd):
    """Run a command and return its stdout."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return result.stdout.strip()


def main(nonprod_acr, prod_acr, image_repo, image_tag, nonprod_user, nonprod_pass, prod_user, prod_pass):
    nonprod_login = nonprod_acr if '.' in nonprod_acr else f"{nonprod_acr}.azurecr.io"

    # Check if tag exists in prod registry
    try:
        tags_output = run([
            "az", "acr", "repository", "show-tags",
            "--name", prod_acr,
            "--repository", image_repo,
            "--output", "tsv"
        ])
        if image_tag in tags_output.splitlines():
            print(f"Image {image_repo}:{image_tag} already exists in {prod_acr}")
            return
    except subprocess.CalledProcessError:
        # Repository may not exist yet; proceed with import
        pass

    print(f"Promoting {image_repo}:{image_tag} from {nonprod_acr} to {prod_acr}")

    # Authenticate to the target registry so the import command can push the image
    run(["az", "acr", "login", "--name", prod_acr, "--username", prod_user, "--password", prod_pass])

    # Import the image into prod
    run([
        "az", "acr", "import",
        "--name", prod_acr,
        "--source", f"{nonprod_login}/{image_repo}:{image_tag}",
        "--image", f"{image_repo}:{image_tag}",
        "--username", nonprod_user,
        "--password", nonprod_pass,
    ])


if __name__ == "__main__":
    if len(sys.argv) != 9:
        print(
            "Usage: promote_acr.py <nonprod_acr> <prod_acr> <image_repo> <image_tag> "
            "<nonprod_user> <nonprod_pass> <prod_user> <prod_pass>"
        )
        sys.exit(1)
    main(*sys.argv[1:])
