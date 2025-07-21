#!/bin/bash
set -o pipefail -e

source ${GITHUB_ACTION_PATH}/../shared/library.sh
cp ${GITHUB_ACTION_PATH}/../shared/settings.xml ./settings.xml

export REPO_NAME=${GITHUB_REPOSITORY#$GITHUB_REPOSITORY_OWNER/}

if [ -n "$track" ]; then
  track=$(echo $track | sed -e 's/track//')
  e=$(echo $e$track)
fi

for env in $(find ${GITHUB_WORKSPACE}/.github/workflows/helm_vars -maxdepth 1 -mindepth 1 -type d -name "$e*") ; do
env=${env%*/}
env_short=${env##*/}
replicas_num=$(grep -s "replica" ${GITHUB_WORKSPACE}/.github/workflows/helm_vars/$env_short/values.yaml | sed 's/replica:\ //')

if [ -z "$replicas_num" ] || [ $replicas_num -eq 0 ]; then
  echo "Skipping e2e tests Allure Report for $env_short as it's not deployed there"
  echo "There's no new Allure Report for $env_short environment. The next step - Allure Report publishing - will probably be skipped."
  echo "skip_allure_report=true" >> $GITHUB_OUTPUT
else

rm -rf ./${INPUT_ALLURE_RESULTS}-$env_short || true
echo "Generating the Allure Report for $env_short"
mv ${GITHUB_WORKSPACE}/allure-results-folder-for-$env_short ./${INPUT_ALLURE_RESULTS}-$env_short

mkdir -p ./${INPUT_GH_PAGES}
mkdir -p ./${INPUT_ALLURE_HISTORY}
rsync -lrvq --exclude=.git ./${INPUT_GH_PAGES}/. ./${INPUT_ALLURE_HISTORY}

REPOSITORY_OWNER_SLASH_NAME=${INPUT_GITHUB_REPO}
REPOSITORY_NAME=${REPOSITORY_OWNER_SLASH_NAME##*/}
GITHUB_PAGES_WEBSITE_URL="https://${INPUT_GITHUB_REPO_OWNER}.github.io/${REPOSITORY_NAME}"

if [[ ${INPUT_REPORT_URL} != '' ]]; then
    GITHUB_PAGES_WEBSITE_URL="${INPUT_REPORT_URL}"
    echo "Replacing github pages url with user input. NEW url ${GITHUB_PAGES_WEBSITE_URL}"
fi

COUNT=$( ( ls ./${INPUT_ALLURE_HISTORY} | wc -l ) )
echo "count folders in allure-history: ${COUNT}"
echo "keep reports count ${INPUT_KEEP_REPORTS}"
INPUT_KEEP_REPORTS=$((INPUT_KEEP_REPORTS+1))
echo "if ${COUNT} > ${INPUT_KEEP_REPORTS}"
if (( COUNT > INPUT_KEEP_REPORTS )); then
  cd ./${INPUT_ALLURE_HISTORY}
  echo "remove index.html last-history"
  rm index.html last-history -rv
  echo "remove old reports"
  ls | sort -n | grep -v 'CNAME' | head -n -$((${INPUT_KEEP_REPORTS}-2)) | xargs rm -rv;
  cd ${GITHUB_WORKSPACE}
fi

#echo "index.html"
echo "Add the redirection in the main index.html"
echo "<!DOCTYPE html><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"0; URL=${GITHUB_PAGES_WEBSITE_URL}/${INPUT_GITHUB_RUN_NUM}-$env_short/index.html\">" > ./${INPUT_ALLURE_HISTORY}/index.html # path
echo "<meta http-equiv=\"Pragma\" content=\"no-cache\"><meta http-equiv=\"Expires\" content=\"0\">" >> ./${INPUT_ALLURE_HISTORY}/index.html

#echo "executor.json"
echo "Generating executor.json file"
echo "{\"name\":\"GitHub Actions\",\"type\":\"github\",\"reportName\":\"Allure Report for ${REPO_NAME} on ${env_short}\"," > executor.json
echo "\"url\":\"${GITHUB_PAGES_WEBSITE_URL}\"," >> executor.json # ???
echo "\"reportUrl\":\"${GITHUB_PAGES_WEBSITE_URL}/${INPUT_GITHUB_RUN_NUM}-$env_short/\"," >> executor.json
echo "\"buildUrl\":\"${INPUT_GITHUB_SERVER_URL}/${INPUT_GITHUB_TESTS_REPO}/actions/runs/${INPUT_GITHUB_RUN_ID}\"," >> executor.json
echo "\"buildName\":\"GitHub Actions Run #${INPUT_GITHUB_RUN_ID}\",\"buildOrder\":\"${INPUT_GITHUB_RUN_NUM}\"}" >> executor.json
cp executor.json ./${INPUT_ALLURE_RESULTS}-$env_short/executor.json || true

#environment.properties
echo "Create the environment.properties file"
echo "ENV=$env_short" >> ./${INPUT_ALLURE_RESULTS}-$env_short/environment.properties
#cp ${GITHUB_WORKSPACE}/allure_temp.environment.properties ./${INPUT_ALLURE_RESULTS}/environment.properties || true

echo "keep allure history from ${INPUT_GH_PAGES}/last-history to ${INPUT_ALLURE_RESULTS}/history"
cp -r ./${INPUT_GH_PAGES}/last-history/. ./${INPUT_ALLURE_RESULTS}-$env_short/history || true

echo "generating report from ${INPUT_ALLURE_RESULTS} to ${INPUT_ALLURE_REPORT} ..."
allure generate --clean ${INPUT_ALLURE_RESULTS}-$env_short -o ${INPUT_ALLURE_REPORT}-$env_short

echo "copy allure-report to ${INPUT_ALLURE_HISTORY}/${INPUT_GITHUB_RUN_NUM}-$env_short"
cp -r ./${INPUT_ALLURE_REPORT}-$env_short/. ./${INPUT_ALLURE_HISTORY}/${INPUT_GITHUB_RUN_NUM}-$env_short
echo "copy allure-report history to /${INPUT_ALLURE_HISTORY}/last-history"
cp -r ./${INPUT_ALLURE_REPORT}-$env_short/history/. ./${INPUT_ALLURE_HISTORY}/last-history

# numbers from Allure Report summary
allure_total=$(cat ${INPUT_ALLURE_REPORT}-$env_short/widgets/summary.json | jq -r '.statistic.total')
allure_passed=$(cat ${INPUT_ALLURE_REPORT}-$env_short/widgets/summary.json | jq -r '.statistic.passed')
allure_failed=$(cat ${INPUT_ALLURE_REPORT}-$env_short/widgets/summary.json | jq -r '.statistic.failed')
allure_broken=$(cat ${INPUT_ALLURE_REPORT}-$env_short/widgets/summary.json | jq -r '.statistic.broken')

# colors
color_total="📗"
color_passed="✅"
color_failed="❌"
color_broken="💔"

echo "We're not skipping the Allure Report publishing for $env_short environment in the next step"
echo "skip_allure_report=false" >> $GITHUB_OUTPUT
echo "Create the Allure Report output for $env_short with URL to an appropriate report"
echo ":bar_chart: Allure Report for [$env_short](https://$GITHUB_REPOSITORY_OWNER.github.io/$REPO_NAME/${INPUT_GITHUB_RUN_NUM}-$env_short/index.html) environment. Total cases $color_total $allure_total: $color_passed $allure_passed, $color_failed $allure_failed, $color_broken $allure_broken.\n" >> allure_urls.txt

fi

done

payload=$(cat allure_urls.txt)
echo "allure_url<<EOF"$'\n'"$payload"$'\n'EOF >> "$GITHUB_OUTPUT"
