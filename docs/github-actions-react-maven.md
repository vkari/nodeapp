# GitHub Actions for React and Maven Applications

This page describes the typical GitHub Actions configuration for projects that use both a React front end and a Maven-based Java backend. The examples below can be copied into your own pipelines or adapted to meet your specific needs.

## Directory Structure

Assume your repository is organized with a `frontend` directory that contains the React code and a `backend` directory with the Maven project:

```
my-app/
├── backend/       # Maven project (pom.xml)
└── frontend/      # React project (package.json)
```

## Overview of Workflow

1. **Checkout the code**.
2. **Set up Node.js** to install and build the React application.
3. **Set up Java and Maven** for the backend.
4. **Run unit tests** for both the frontend and backend.
5. **Build the Docker image** (optional).
6. **Deploy** or publish artifacts if the pipeline is triggered on the main branch or a release tag.

## Example GitHub Actions Workflow

Create a workflow file under `.github/workflows/build.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
      working-directory: frontend

    - name: Install frontend dependencies
      run: npm ci
      working-directory: frontend

    - name: Build React app
      run: npm run build
      working-directory: frontend

    - name: Set up Java
      uses: actions/setup-java@v3
      with:
        distribution: 'temurin'
        java-version: '17'
        cache: 'maven'
      working-directory: backend

    - name: Build backend
      run: mvn -B package
      working-directory: backend

    - name: Run backend tests
      run: mvn -B test
      working-directory: backend

    - name: Run frontend tests
      run: npm test -- --watchAll=false
      working-directory: frontend
```

This workflow installs dependencies, builds both applications, and runs tests for each. You can extend it to push Docker images or deploy artifacts as needed.

## Additional Tips

- Use separate jobs for frontend and backend if you want to run them in parallel.
- Cache dependencies using the built-in options from `actions/setup-node` and `actions/setup-java` for faster builds.
- Store sensitive values such as API keys in repository secrets and reference them in your workflow.
- Include a SonarQube or other code quality scan step if required.

## Automated Deployment

You can extend the workflow with a dedicated deployment job that runs after the build completes. The basic idea is to reuse the artifacts produced by the build step and push them to your target environment:

```yaml
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Configure credentials
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy application
        run: ./deploy.sh ${{ github.sha }}
```

### Akamai CDN

If you host your static assets on Akamai, add a step to purge the CDN after deployment so clients receive the latest version:

```yaml
- name: Purge Akamai cache
  uses: akamai/cli-action@v1
  with:
    edgerc: ${{ secrets.AKAMAI_EDGERC }}
    section: default
    urls: 'https://example.com/*'
```

### Redis Cache

During integration tests or for session management you may rely on Redis. GitHub Actions allows you to spin up a Redis container or connect to an existing instance:

```yaml
- name: Start Redis
  uses: supercharge/redis-github-action@v1
```

Automated deployment (often shortened to **ADA** in this context) ensures your application is continuously delivered without manual intervention, while still allowing you to insert approval gates if needed.

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [React documentation](https://react.dev/)
- [Maven documentation](https://maven.apache.org/)

