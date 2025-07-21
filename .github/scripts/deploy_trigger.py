import os
import subprocess
import yaml
import json
from pathlib import Path

def run(cmd):
    print(f"👉 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout.decode()
        print(output)
        return output
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e.cmd}")
        print(e.output.decode())
        raise

def set_env():
    required_vars = [
        "resourcegroup", "clustername", "namespace", "DOCKER_TAG",
        "environment", "acr_name", "app_type", "chartpath", "valuespath"
    ]
    for var in required_vars:
        if not os.getenv(var):
            print(f"⚠️  Missing required env var: {var}")

    os.environ["RESOURCE_GROUP"] = os.getenv("resourcegroup")
    os.environ["CLUSTER_NAME"] = os.getenv("clustername")
    os.environ["K8S_NAMESPACE"] = os.getenv("namespace")
    os.environ["DOCKER_TAG"] = os.getenv("DOCKER_TAG")
    os.environ["REPO_NAME"] = os.getenv("GITHUB_REPOSITORY", "").split("/")[-1]
    os.environ["DEPLOY_ENV"] = os.getenv("environment")
    os.environ["DEBUG_MODE"] = os.getenv("debug", "false")
    os.environ["APP_TYPE"] = os.getenv("app_type")
    os.environ["CHART_PATH"] = os.getenv("chartpath")
    os.environ["VALUES_PATH"] = os.getenv("valuespath")
    os.environ["AZURE_CONTAINER_REGISTRY"] = f"{os.getenv('acr_name')}.azurecr.io"

    print("🔧 Environment Variables Set:")
    for k in ["RESOURCE_GROUP", "CLUSTER_NAME", "K8S_NAMESPACE", "DOCKER_TAG", "REPO_NAME", "DEPLOY_ENV", "APP_TYPE", "CHART_PATH", "VALUES_PATH", "AZURE_CONTAINER_REGISTRY"]:
        print(f"  - {k}: {os.environ[k]}")

def set_kube_context():
    run(f"az aks get-credentials --resource-group {os.environ['RESOURCE_GROUP']} --name {os.environ['CLUSTER_NAME']} --overwrite-existing")

def update_values(values_file: Path):
    print(f"🔧 Updating Helm values in {values_file}")
    with open(values_file, 'r') as f:
        values = yaml.safe_load(f)

    values["namespace"] = os.environ["K8S_NAMESPACE"]
    values["registry"] = f"{os.environ['AZURE_CONTAINER_REGISTRY']}/{os.environ['REPO_NAME']}"
    values["tag"] = os.environ["DOCKER_TAG"]
    values["appPort"] = 3000 if os.environ["APP_TYPE"] == "nodejs" else 8080

    with open(values_file, 'w') as f:
        yaml.dump(values, f)

def deploy_helm(release_name: str, values_path: str):
    update_values(Path(values_path))
    debug_flag = "--debug" if os.environ.get("DEBUG_MODE") == "true" else ""

    print(f"\u2139\ufe0f  Pre-deployment check for {release_name}")
    run(
        f"kubectl get deployment {release_name} -n {os.environ['K8S_NAMESPACE']} "
        f"--context {os.environ['CLUSTER_NAME']} -o wide || true"
    )
    run(
        f"kubectl get pods -n {os.environ['K8S_NAMESPACE']} "
        f"--context {os.environ['CLUSTER_NAME']} "
        f"--selector app.kubernetes.io/name={release_name} || true"
    )

    cmd = (
        f"helm upgrade --install {release_name} {os.environ['CHART_PATH']} "
        f"-f {values_path} --namespace {os.environ['K8S_NAMESPACE']} "
        f"{debug_flag} --wait --timeout 15m"
    )
    run(cmd)

def main():
    print("🚀 Starting Python-based Helm Deployment...")
    set_env()

    deploy_envs_raw = os.environ.get("deployEnvs", "")
    deploy_envs = deploy_envs_raw.strip("[]").replace('"', '').replace("'", "").split(",")
    deploy_envs = [env.strip() for env in deploy_envs if env.strip()]

    if not deploy_envs:
        print("⚠️ No deploy environments detected. Exiting.")
        return

    chart_path = os.environ["CHART_PATH"]
    repo_name = os.environ["REPO_NAME"]
    app_type = os.environ["APP_TYPE"]

    for env in deploy_envs:
        print(f"\n🚀 Starting deployment for environment: {env}")
        os.environ["DEPLOY_ENV"] = env
        os.environ["environment"] = env

        # Re-resolve cluster, namespace, etc. per env
        deploy_config = json.loads(Path("resolved.json").read_text())
        space = deploy_config.get("deploy", {}).get("spaces", {}).get(env) or \
                deploy_config.get("deploy", {}).get("production", {}).get("spaces", {}).get(env, {})

        os.environ["K8S_NAMESPACE"] = space.get("namespace", "")
        os.environ["CLUSTER_NAME"] = space.get("cluster", "")
        os.environ["VALUES_PATH"] = f"{chart_path}/helm_vars/{env}/values.yaml"

        set_kube_context()

        if app_type == "nodejs":
            print("🔄 React app detected - Deploying AUTH then LIVE")
            deploy_helm(f"{repo_name}-auth", f"{chart_path}/helm_vars/{env}/values.auth.yaml")
            deploy_helm(repo_name, f"{chart_path}/helm_vars/{env}/values.yaml")
        else:
            print("📦 Maven app detected - Deploying LIVE only")
            deploy_helm(repo_name, os.environ["VALUES_PATH"])


if __name__ == "__main__":
    main()
