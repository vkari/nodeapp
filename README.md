# nodeapp

This repository deploys Helm charts via GitHub Actions. Splunk HEC tokens are injected during deployment and are **not** stored in the repo.

Configure the following secrets in your repository settings:

- `SPLUNK_TOKEN_PROD` – used for production deployments
- `SPLUNK_TOKEN_NONPROD` – used for non‑production deployments
- `AKAMAI_EDGERC` – contents of the Akamai credentials file used when purging cache

These values are passed to the deploy workflows and written into Helm values at runtime.

When `akamaiCacheClear` is enabled in the trusted configuration, the workflow
purges Akamai cache using the `cp_codes` defined for the deployment environment
in its `config.yaml`. These codes are exposed via the `AKAMAI_CP_CODES`
environment variable and passed to the purge script automatically.

If the feature flag is omitted, cache clearing defaults to **enabled** for
non-production environments and **disabled** for production deployments.
