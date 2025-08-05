# nodeapp

This repository deploys Helm charts via GitHub Actions. Splunk HEC tokens are injected during deployment and are **not** stored in the repo.

Configure the following secrets in your repository settings:

- `SPLUNK_TOKEN_PROD` – used for production deployments
- `SPLUNK_TOKEN_NONPROD` – used for non‑production deployments
- `AKAMAI_EDGERC` – contents of the Akamai credentials file used when purging cache

These values are passed to the deploy workflows and written into Helm values at runtime.

Set `akamaiCacheClear` in each repository's `config.yaml` under the `deploy`
section. Use `deploy.akamaiCacheClear` for non‑production and
`deploy.production.akamaiCacheClear` for production. When enabled, the workflow
purges Akamai cache using the `cp_codes` listed for the target environment.
These codes are written to the `AKAMAI_CP_CODES` environment variable and passed
to the purge script automatically. If no flag is provided, non‑production
defaults to enabled and production defaults to disabled.
