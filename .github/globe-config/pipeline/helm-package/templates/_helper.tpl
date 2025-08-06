{{/* vim: set filetype=mustache: */}}
{{/*
Generate a unique name for resources based on the release name.
*/}}
{{- define "name" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}


{{/*
Image Repository
*/}}
{{- define "image.repo" -}}
{{- $repo := "" -}}
{{- if .Values.global.sofySolutionContext -}}
{{- $repo = .Values.global.hclImageRegistry -}}
{{- else -}}
{{- $repo = .Values.service.imageRepo -}}
{{- end -}}
{{- if hasSuffix "/" $repo -}}
{{ print $repo }}
{{- else -}}
{{ printf "%s/" $repo }}
{{- end -}}
{{- end -}}

{{/* splunk
Convert memory value from resources.limit to numeric value in MiB to be used by otel memory_limiter processor.
*/}}
{{- define "splunk-otel-collector.convertMemToMib" -}}
{{- $mem := lower . -}}
{{- if hasSuffix "g" $mem -}}
{{- trimSuffix "g" $mem | atoi | mul 1000 -}}
{{- else if hasSuffix "gi" $mem -}}
{{- trimSuffix "gi" $mem | atoi | mul 1024 -}}
{{- else if hasSuffix "mi" $mem -}}
{{- trimSuffix "mi" $mem | atoi -}}
{{- end -}}
{{- end -}}



{{- define "convertYamlToProperties" -}}
{{- range $key, $value := . -}}
{{ $key }}={{ $value | quote }}
{{ end -}}
{{- end -}}



{{- define "getSecret" -}}
{{- $secret := .Values.secrets.clientSecret -}}
{{- $secretObj := (lookup "v1" "Secret" .Release.Namespace $secret.name) -}}
{{- $secretValue := index $secretObj.data $secret.key | b64dec -}}
{{- $secretValue -}}
{{- end -}}

{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "redis-subchart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "redis-subchart.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "redis-subchart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "redis-subchart.labels" -}}
helm.sh/chart: {{ include "redis-subchart.chart" . }}
{{ include "redis-subchart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "redis-subchart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "redis-subchart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "redis-subchart.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "redis-subchart.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}
