# nodeapp

This repository deploys Helm charts via GitHub Actions. Splunk HEC tokens are injected during deployment and are **not** stored in the repo.

Configure the following secrets in your repository settings:

- `SPLUNK_TOKEN_PROD` – used for production deployments
- `SPLUNK_TOKEN_NONPROD` – used for non‑production deployments

These values are passed to the deploy workflows and written into Helm values at runtime.
