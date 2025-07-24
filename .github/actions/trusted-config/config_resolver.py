import os
import yaml
import json
from pathlib import Path
from fnmatch import fnmatch

def load_yaml(path):
    if path.exists():
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️ Failed to load {path}: {e}")
    else:
        print(f"⚠️ File not found: {path}")
    return {}

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            if isinstance(v, bool):
                v = str(v).lower()
            items.append((new_key, v))
    return dict(items)

def get_branch_env(config, branch_name):
    branches = config.get("deploy", {}).get("autoDeployBranches", {})
    branch_config = branches.get(branch_name, {})
    auto_deploy = branch_config.get("autoDeploy", False)
    envs = branch_config.get("env", [])
    return (envs[0] if auto_deploy and envs else ""), auto_deploy, envs

# === Context Info ===
repo_full = os.environ.get("GITHUB_REPOSITORY", "")
repo_name = repo_full.split("/")[-1] if "/" in repo_full else ""
org_name = repo_full.split("/")[0] if "/" in repo_full else ""
branch_name = os.environ.get("GITHUB_REF_NAME", "main").replace("/", ".")

print(f"📦 Repository: {repo_name}")
print(f"🏢 Org: {org_name}")
print(f"🔀 Branch: {branch_name}")

# === File Paths ===
workspace = Path(os.environ.get("GITHUB_WORKSPACE", "."))
base_path = workspace / "commons/.github/globe-config"

common_config_path = base_path / "commonConfig.yaml"
project_config_path = base_path / f"{org_name}/projectConfig.yaml"
repo_config_path = base_path / f"{org_name}/{repo_name}/config.yaml"
resolved_json_path = Path("resolved.json")
resolved_env_path = Path("resolved.env")

# === Load and Merge Config ===
resolved_config = {}
resolved_config.update(load_yaml(common_config_path))
resolved_config.update(load_yaml(project_config_path))
resolved_config.update(load_yaml(repo_config_path))

# === Promote Key Settings ===
app = resolved_config.get("app", {})
app_maven = app.get("maven", {})
app_node = app.get("node", {})
app_sonar = app.get("sonar", {})
features = resolved_config.get("features", {})
acr = resolved_config.get("acr", {})
deploy = resolved_config.get("deploy", {})
manual_cfg = deploy.get("manualApproval", {})

# SonarQube enabled flag
sonar_enabled = (
    app_sonar.get("enableSonar")
    if "enableSonar" in app_sonar
    else app_sonar.get("enabled", False)
)

resolved_config.update({
    "appType": app_maven.get("appType") or app_node.get("appType", ""),
    "enableSonar": sonar_enabled,
    "javaVersion": app_maven.get("javaVersion", "21"),
    "mavenVersion": app_maven.get("mavenVersion", "3.9.6"),
    "mavenArgs": app_maven.get("mavenArgs", ""),
    "nodeVersion": app_node.get("nodeVersion", ""),
    "nodeInstallArgs": app_node.get("nodeInstallArgs", ""),
    "nodeBuildArgs": app_node.get("nodeBuildArgs", ""),
    "nodeTestArgs": app_node.get("nodeTestArgs", ""),
    "buildDeploy": app_node.get("buildDeploy", False) or app_maven.get("buildDeploy", False),
    "cd": app_node.get("cd", False) or app_maven.get("cd", False),
    "publishGit": app_maven.get("publishGit") or app_node.get("publishGit", False),
    "sonarProjectName": app_sonar.get("sonarProjectName", ""),
    "akamaiCacheClear": False,
    "redisCacheClear": features.get("redisCacheClear", False),
    "scanning": features.get("scanning", False),
    "acrProd": acr.get("prod", ""),
    "acrNonprod": acr.get("nonprod", ""),
    "manualProdApproval": manual_cfg.get("prod", False),
    "manualNonProdApproval": manual_cfg.get("nonprod", False)
})
skip_qg_val = app_sonar.get("skipQualityGate", False)
# === Resolve Environments ===
environment, auto_deploy, envs = get_branch_env(resolved_config, branch_name)
override_env = os.environ.get("INPUT_ENVIRONMENT", "").strip()
if override_env:
    print(f"🔧 Override environment input detected: {override_env}")
    environment = override_env
    if override_env not in envs:
        envs = [override_env]
if not envs:
    default_env = deploy.get("default_environments", "")
    if default_env:
        envs = [default_env]
        if not environment:
            environment = default_env
if not environment:
    environment = deploy.get("default_environments", "")
resolved_config["environment"] = environment
resolved_config["autoDeploy"] = auto_deploy
resolved_config["deployEnvs"] = envs

# === Determine Akamai Cache Clear Flag ===
env_clear_flag = None
if environment in deploy.get("production", {}).get("spaces", {}):
    env_clear_flag = deploy.get("production", {}).get("akamaiCacheClear")
else:
    env_clear_flag = deploy.get("akamaiCacheClear")

flag = not str(environment).startswith("p") if env_clear_flag is None else env_clear_flag
if "akamaiCacheClear" in features:
    flag = features.get("akamaiCacheClear")

resolved_config["akamaiCacheClear"] = flag

print(f"🚀 Auto Deploy Enabled: {auto_deploy}")
print(f"🌍 Target Environments: {envs}")
skip_quality_gate = False
patterns = []
if isinstance(skip_qg_val, bool):
    skip_quality_gate = skip_qg_val
elif isinstance(skip_qg_val, list):
    patterns = [str(p).strip() for p in skip_qg_val if str(p).strip()]
else:
    patterns = [p.strip() for p in str(skip_qg_val).split(',') if p.strip()]

if not skip_quality_gate and patterns:
    branch_candidates = [branch_name]
    head_ref = os.environ.get("GITHUB_HEAD_REF", "")
    base_ref = os.environ.get("GITHUB_BASE_REF", "")
    if head_ref:
        branch_candidates.append(head_ref.replace("/", "."))
    if base_ref:
        branch_candidates.append(base_ref.replace("/", "."))
    for candidate in branch_candidates:
        for pat in patterns:
            if fnmatch(candidate, pat):
                skip_quality_gate = True
                break
        if skip_quality_gate:
            break

resolved_config["skipQualityGate"] = skip_quality_gate

# === Namespace, Cluster and Flags ===
production_cfg = deploy.get("production", {})
prod_spaces = production_cfg.get("spaces", {})

if environment in prod_spaces:
    space = prod_spaces.get(environment, {})
    dryrun_flag = production_cfg.get("dryrun", False)
    verbose_flag = production_cfg.get("verbose", False)
else:
    space = deploy.get("spaces", {}).get(environment, {})
    dryrun_flag = deploy.get("dryrun", False)
    verbose_flag = deploy.get("verbose", False)

resolved_config["port"] = space.get("port")
resolved_config["namespace"] = space.get("namespace")
cluster = space.get("cluster", "")
resolved_config["cluster"] = cluster
resolved_config["aem_env"] = space.get("aem_env", "")
resolved_config["akamai_cp_codes"] = space.get("cp_codes", [])

# === Resource Group Logic derived from cluster
resourcegroup = space.get("resourcegroup")
if not resourcegroup:
    if "p-eastus2" in cluster:
        resourcegroup = "rg-wcs-prod-eastus2"
    elif "p-centralus" in cluster:
        resourcegroup = "rg-wcs-prod-centralus"
    elif "n-centralus" in cluster:
        resourcegroup = "rg-wcs-nonprod-centralus"
    else:
        resourcegroup = "rg-wcs-nonprod-eastus2"

resolved_config["resourcegroup"] = resourcegroup
resolved_config["dryrun"] = dryrun_flag
resolved_config["verbose"] = verbose_flag

# === Output JSON + ENV ===
print("✅ Final Merged Config:")
print(json.dumps(resolved_config, indent=2))

with open(resolved_json_path, "w") as f:
    json.dump(resolved_config, f, indent=2)

flat_env = flatten_dict(resolved_config)
with open(resolved_env_path, "w") as f:
    for k, v in flat_env.items():
        f.write(f"{k}={v}\n")

print("✅ Wrote resolved.json and resolved.env")

# === GitHub Actions Output ===
output_file = os.environ.get("GITHUB_OUTPUT")
if output_file:
    with open(output_file, "a") as f:
        f.write(f"deployEnvsJson={json.dumps(envs)}\n")
        f.write(f"autoDeploy={str(auto_deploy).lower()}\n")
        f.write(f"aemEnv={space.get('aem_env', '')}\n")
        f.write(f"cpCodes={json.dumps(space.get('cp_codes', []))}\n")
        f.write(f"buildDeploy={str(app_node.get('buildDeploy', False) or app_maven.get('buildDeploy', False)).lower()}\n")
        f.write(f"skipQualityGate={str(resolved_config.get('skipQualityGate', False)).lower()}\n")
