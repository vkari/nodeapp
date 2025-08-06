# nodeapp

This repository deploys Helm charts via GitHub Actions. Splunk HEC tokens are injected during deployment and are **not** stored in the repo.

Configure the following secrets in your repository settings:

For React applications:

- `SPLUNK_TOKEN_PROD` – used for production deployments
- `SPLUNK_TOKEN_NONPROD` – used for non‑production deployments

For microservices or other Maven-based applications:

- `SPLUNK_TOKEN_PROD_MS` – used for production deployments
- `SPLUNK_TOKEN_NONPROD_MS` – used for non‑production deployments

Use the token pair that matches your application type; the deploy workflows
inject the appropriate value into the Helm chart at runtime.
