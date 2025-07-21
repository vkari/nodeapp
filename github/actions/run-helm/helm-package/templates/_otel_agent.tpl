{{/*
Config for the otel-collector agent
The values can be overridden in .Values.agent.config
*/}}
{{- define "splunk-otel-collector.agentConfig" -}}
exporters:
  splunk_hec/platform_logs:
    endpoint: {{ .Values.splunk.endpoint | quote }}
    token: "${SPLUNK_PLATFORM_HEC_TOKEN}"
    index: {{ .Values.splunk.index | quote }}
    source: {{ .Values.splunk.source | quote }}
    max_idle_conns: {{ .Values.splunk.maxConnections }}
    max_idle_conns_per_host: {{ .Values.splunk.maxConnections }}
    disable_compression: {{ .Values.splunk.disableCompression }}
    timeout: {{ .Values.splunk.timeout }}
    idle_conn_timeout: {{ .Values.splunk.idleConnTimeout }}
    splunk_app_name: {{ .Values.splunk.app_name }}
    splunk_app_version: {{ .Values.splunk.app_version }}
    profiling_data_enabled: false
    tls:
      insecure_skip_verify: {{ .Values.splunk.insecureSkipVerify }}
      {{- if .Values.splunk.clientCert }}
      cert_file: /otel/etc/splunk_platform_hec_client_cert
      {{- end }}
      {{- if .Values.splunk.clientKey  }}
      key_file: /otel/etc/splunk_platform_hec_client_key
      {{- end }}
      {{- if .Values.splunk.caFile }}
      ca_file: /otel/etc/splunk_platform_hec_ca_file
      {{- end }}
    retry_on_failure:
      enabled: {{ (.Values.splunk.retryOnFailure).enabled }}
      initial_interval: {{ (.Values.splunk.retryOnFailure).initialInterval }}
      max_interval: {{ (.Values.splunk.retryOnFailure).maxInterval }}
      max_elapsed_time: {{ (.Values.splunk.retryOnFailure).maxElapsedTime }}
    sending_queue:
      enabled:  {{ (.Values.splunk.sendingQueue).enabled }}
      num_consumers: {{ (.Values.splunk.sendingQueue).numConsumers }}
      queue_size: {{ (.Values.splunk.sendingQueue).queueSize }}

extensions:
  file_storage:
    directory: {{ .Values.splunk.checkpointPath }}
  memory_ballast:
    size_mib: ${SPLUNK_BALLAST_SIZE_MIB}
  health_check: null
  zpages: null

processors:
  batch: null
  memory_limiter:
  # check_interval is the time between measurements of memory usage.
    check_interval: 2s
  # By default limit_mib is set to 90% of container memory limit
    limit_mib: ${SPLUNK_MEMORY_LIMIT_MIB}
  resource:
    attributes:
    - action: insert
      key: node.name
      value: ${K8S_NODE_NAME}
    - action: upsert
      key: k8s.container.name
      value: {{ .Values.splunk.containerName }}
  resource/add_agent_k8s:
    attributes:
    - action: insert
      key: pod
      value: ${K8S_POD_NAME}
    - action: insert
      key: pod.uid
      value: ${K8S_POD_UID}
    - action: insert
      key: namespace
      value: ${K8S_NAMESPACE}
  resourcedetection:
    detectors:
    - env
    - system
    override: true
    timeout: 10s

receivers:
  filelog:
    start_at: beginning
    include_file_path: true
    include_file_name: false
    poll_interval: 200ms
    max_concurrent_files: 1024
    include:{{- toYaml .Values.splunk.filelogpath | nindent 4 }}
    encoding: utf-8
    exclude: null
    fingerprint_size: 1kb
    max_log_size: 1MiB
    force_flush_period: "0"
    storage: file_storage
    operators:
    - from: attributes["log.file.path"]
      to: resource["com.splunk.source"]
      type: move
    - field: resource["com.splunk.sourcetype"]
      type: add
      value: ${K8S_POD_NAME}

service:
  extensions:
  - file_storage
  - health_check
  - memory_ballast
  - zpages
  pipelines:
    logs:
      exporters:
      - splunk_hec/platform_logs
      processors:
      - memory_limiter
      - batch
      - resource
      - resource/add_agent_k8s
      - resourcedetection
      receivers:
      - filelog
{{ end }}