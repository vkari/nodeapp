# 🚀 GitHub Workflows – TSC CI/CD

This repository provides **reusable GitHub Actions workflows** and shared configurations to support automated CI/CD pipelines for **microservices** and **React applications** across the Tractor Supply ecosystem.

---

## 🔁 Reusable Workflows

### `tsc-pr-workflow.yaml`
Runs pull request validation for all application types:
- Executes unit tests and builds
- Dispatches either `maven-build` or `react-build` composite actions based on project type

### `tsc-cicd-workflow.yaml`
Primary CI/CD pipeline for **non-production and production environments**:
- Publishes artifacts
- Runs SonarCloud static analysis
- Performs Helm deployments using the appropriate action
> ✅ **Production deployment support is now implemented**

### `deploy-env.yaml`
Supports **manual or reusable environment deployments**:
- Triggers `non-prod-deploy`
- Finalizes deployment with GitHub commit status updates

> ⚠️ CD support for React applications is still under development

---

## 🌍 Global Configuration (`Globe Config`)

This repo contains environment- and org-level configuration for pipelines.

### 🔧 Organization-Level Configuration

- **`commonConfig.yaml`**
  Sets defaults shared across all orgs – e.g., tool versions, secrets, flags.

- **`Tractor-Supply-Ecommerce/projectConfig.yaml`**
  Provides organization-specific overrides for apps under `Tractor-Supply-Ecommerce`.

### 📁 Repository-Level Configuration

Each application repository has a corresponding folder inside `Tractor-Supply-Ecommerce/`.
This folder must:
- Match the repository name
- Contain a `config.yaml` that customizes behavior for that repo

#### Examples

| App Type        | Example Repo                                                                 |
|-----------------|------------------------------------------------------------------------------|
| React App       | [`tsc-nextjs-pdp`](Tractor-Supply-Ecommerce/tsc-nextjs-pdp/config.yaml)      |
| Maven Microservice | [`tsc-bulk-quote-service`](Tractor-Supply-Ecommerce/tsc-bulk-quote-service/config.yaml) |

---

## 🚀 Launching a New Application

1. Create a new directory under `Tractor-Supply-Ecommerce/` matching the GitHub repo name
2. Add a `config.yaml` modeled after an existing example
3. Commit and push – reusable workflows will automatically pick it up

---

## 📄 Example Workflow File

Below is a sample workflow (`TSC-Workflow-build-deploy.yaml`) for app repos that uses the reusable workflows defined in this library:

```yaml
name: TSC React Workflow

on:
  push:
    branches:
      - main
      - develop
      - 'M2025**.[0-9][0-9].[0-9][0-9]'
      - 'R2025**.[0-9][0-9].[0-9][0-9]'
  pull_request:
    branches:
      - main
      - develop
      - 'M2025**.[0-9][0-9].[0-9][0-9]'
      - 'R2025**.[0-9][0-9].[0-9][0-9]'

jobs:
  ci-cd:
    if: github.event_name == 'push'
    name: "🧪 CI/CD | Build, Test & Publish"
    uses: Tractor-Supply-Ecommerce/pipeline-commons-library/.github/workflows/tsc-cicd-workflow.yaml@main
    secrets: inherit

  pr-validation:
    if: github.event_name == 'pull_request'
    name: "🔍 PR | Validate Pull Request"
    uses: Tractor-Supply-Ecommerce/pipeline-commons-library/.github/workflows/tsc-pr-workflow.yaml@main
    secrets: inherit
