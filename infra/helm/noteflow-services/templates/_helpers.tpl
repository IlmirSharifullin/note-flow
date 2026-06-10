{{- define "noteflow-services.labels" -}}
app.kubernetes.io/part-of: noteflow
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end }}

{{- define "noteflow-services.serviceLabels" -}}
{{ include "noteflow-services.labels" .root }}
app.kubernetes.io/name: {{ .service.name }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
{{- end }}
