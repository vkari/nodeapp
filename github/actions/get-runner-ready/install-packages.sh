#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh

# Define the local system release details
AZ_DIST=$(lsb_release -cs)

sudo sed -i -e 's/http:\/\/archive\.ubuntu\.com\/ubuntu\//mirror:\/\/mirrors\.ubuntu\.com\/mirrors.txt/' /etc/apt/sources.list

sudo apt-get update -y
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release software-properties-common jq -y

# Download and install the Microsoft signing key
sudo mkdir -p /etc/apt/keyrings
curl -sLS https://packages.microsoft.com/keys/microsoft.asc |
  gpg --dearmor | sudo tee /etc/apt/keyrings/microsoft.gpg > /dev/null
sudo chmod go+r /etc/apt/keyrings/microsoft.gpg
# add the GPG key for the official Docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
# add the GPG key for Helm 3 repo
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
# download kubelogin
curl -fsSLO https://github.com/Azure/kubelogin/releases/download/v0.1.5/kubelogin-linux-amd64.zip
# download sonar-scanner-cli
curl -fsSLO https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-6.2.1.4610-linux-x64.zip
# Download Allure Report CLI
curl -fsSLO https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.32.0/allure-commandline-2.32.0.tgz

# Add Azure packages repository to APT sourse
echo "Types: deb
URIs: https://packages.microsoft.com/repos/azure-cli/
Suites: ${AZ_DIST}
Components: main
Architectures: $(dpkg --print-architecture)
Signed-by: /etc/apt/keyrings/microsoft.gpg" | sudo tee /etc/apt/sources.list.d/azure-cli.sources
# Add the Docker repository to APT sources
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
# add the Helm 3 repo to APT sources
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list

sudo apt-get update -y
sudo apt-get install maven openjdk-21-jdk azure-cli docker-ce helm -y
sudo update-alternatives --config keytool || true
# Install kubelogin and kubectl
sudo unzip -ojd /usr/local/bin kubelogin-linux-amd64.zip bin/linux_amd64/kubelogin
sudo chmod +x /usr/local/bin/kubelogin
echo kubelogin version is $(kubelogin --version)
# install sonar-scanner-cli
unzip -qq sonar-scanner-cli-6.2.1.4610-linux-x64.zip
mv sonar-scanner-6.2.1.4610-linux-x64 sonar-scanner-cli
sudo chmod +x ./sonar-scanner-cli/bin/sonar-scanner
# install Allure Report cli
tar -xf allure-commandline-2.32.0.tgz
mv allure-2.32.0 allure
chmod -R +x ./allure/bin
