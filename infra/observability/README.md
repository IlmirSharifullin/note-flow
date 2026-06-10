# Observability для NoteFlow

Observability отвечает на три вопроса:

- что сломалось;
- где именно сломалось;
- почему это могло произойти.

Для этого обычно собирают три типа данных:

- метрики: численные показатели, например CPU, память, количество 5xx;
- логи: текстовые события из pod'ов и приложений;
- трейсы: путь одного запроса через несколько сервисов.

## Выбранный стек

Для локального Kubernetes выбран стек:

- Prometheus Operator через `kube-prometheus-stack` - метрики, правила алертов, Alertmanager;
- Grafana - визуализация метрик, логов и трейсов;
- Loki + Promtail - сбор и хранение логов Kubernetes;
- Tempo - хранение трейсов;
- OpenTelemetry Collector - единая точка приема OTLP-трейсов и OTLP-метрик от приложений.

Почему этот вариант:

- он легче, чем ELK и полноценные VictoriaMetrics/VictoriaLogs cluster-установки;
- хорошо подходит для Minikube;
- Grafana умеет работать сразу с Prometheus, Loki, Tempo и Alertmanager;
- OpenTelemetry Collector не привязывает приложение к одному backend'у;
- стек хорошо сочетается с Istio: можно собирать mesh-метрики и потом добавить distributed tracing.

## Рассмотренные варианты

### Prometheus + Loki + Tempo + Grafana

Хороший базовый вариант для учебного и небольшого production-стека.

Плюсы:

- простой вход;
- много готовых Helm chart'ов и dashboard'ов;
- удобно смотреть метрики, логи и трейсы в одном интерфейсе Grafana;
- не требует тяжелого Elasticsearch или ClickHouse.

Минусы:

- Loki хуже подходит для сложной полнотекстовой аналитики логов, чем Elasticsearch;
- для большого production нужно отдельно думать про retention, object storage и HA.

### VictoriaMetrics + VictoriaLogs + Grafana

Хороший вариант, когда метрик и логов становится много.

Плюсы:

- экономное хранение метрик;
- VictoriaMetrics часто проще и дешевле масштабировать, чем классический Prometheus;
- VictoriaLogs может быть легче ELK.

Минусы:

- cluster-режим сложнее для локального стенда;
- больше компонентов для поддержки;
- для учебного Minikube это обычно избыточно.

### Elasticsearch + Logstash + Kibana

Классический стек для логов.

Плюсы:

- мощный поиск по логам;
- гибкая обработка логов через Logstash;
- удобен для сложной лог-аналитики.

Минусы:

- тяжелый по CPU, памяти и диску;
- для локального кластера сложнее и дороже;
- не решает метрики и трейсы без дополнительных компонентов.

### SigNoz

All-in-one observability платформа на базе OpenTelemetry и ClickHouse.

Плюсы:

- метрики, логи и трейсы в одном продукте;
- хорошо дружит с OpenTelemetry;
- меньше ручной сборки интерфейса.

Минусы:

- это отдельная платформа, а не набор стандартных cloud-native компонентов;
- ClickHouse добавляет требования к ресурсам;
- для задания полезнее показать понимание отдельных частей стека.

### Uptrace + OpenTelemetry

Хороший вариант для трейсов и APM.

Плюсы:

- удобен для анализа distributed tracing;
- хорошо работает с OpenTelemetry.

Минусы:

- меньше закрывает Kubernetes-инфраструктуру из коробки;
- все равно нужны Prometheus/Grafana или похожие инструменты для метрик и алертов.

## Что добавлено в репозиторий

Helm values:

- `infra/observability/helm-values/kube-prometheus-stack.yaml`
- `infra/observability/helm-values/loki-stack.yaml`
- `infra/observability/helm-values/tempo.yaml`
- `infra/observability/helm-values/opentelemetry-collector.yaml`

GitOps Applications:

- `infra/gitops/apps/observability-prometheus.yaml`
- `infra/gitops/apps/observability-loki.yaml`
- `infra/gitops/apps/observability-tempo.yaml`
- `infra/gitops/apps/observability-otel.yaml`
- `infra/gitops/apps/observability-platform.yaml`

Kubernetes resources:

- `infra/gitops/platform/observability/namespace.yaml`
- `infra/gitops/platform/observability/service-monitors.yaml`
- `infra/gitops/platform/observability/alerts.yaml`

## Что мониторится

Prometheus собирает:

- Kubernetes API, kubelet, node-exporter, kube-state-metrics;
- Prometheus Operator и Alertmanager;
- Grafana;
- Loki;
- Tempo;
- OpenTelemetry Collector;
- Istio control plane (`istiod`);
- Istio ingress gateway через `PodMonitor`;
- Envoy Rate Limit Service.

## Алерты

Добавлены базовые правила:

- pod часто перезапускается;
- pod долго не готов;
- высокая загрузка памяти на ноде;
- высокий процент 5xx через Istio;
- Rate Limit Service недоступен для Prometheus.

Alertmanager сейчас настроен с простым receiver'ом без внешних интеграций.
Для production обычно добавляют Telegram, Slack, email или webhook в incident-систему.

## Установка вручную

```bash
kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f -

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

helm upgrade --install observability-loki grafana/loki-stack \
  --version 2.10.3 \
  --namespace observability \
  -f infra/observability/helm-values/loki-stack.yaml \
  --wait --timeout 8m

helm upgrade --install observability-tempo grafana/tempo \
  --version 1.24.4 \
  --namespace observability \
  -f infra/observability/helm-values/tempo.yaml \
  --wait --timeout 8m

helm upgrade --install observability prometheus-community/kube-prometheus-stack \
  --version 86.2.2 \
  --namespace observability \
  -f infra/observability/helm-values/kube-prometheus-stack.yaml \
  --wait --timeout 12m

helm upgrade --install observability-otel open-telemetry/opentelemetry-collector \
  --version 0.158.1 \
  --namespace observability \
  -f infra/observability/helm-values/opentelemetry-collector.yaml \
  --wait --timeout 8m

kubectl apply -f infra/gitops/platform/observability
```

## Проверка

```bash
kubectl get pods -n observability
kubectl get prometheus,alertmanager -n observability
kubectl get servicemonitor,podmonitor,prometheusrule -n observability
helm list -n observability
```

Открыть Grafana локально:

```bash
kubectl port-forward -n observability svc/observability-grafana 3000:80
```

Дальше открыть:

```text
http://127.0.0.1:3000
```

Логин:

```text
admin
```

Пароль:

```text
admin
```

В Grafana должны быть datasource:

- Prometheus;
- Alertmanager;
- Loki;
- Tempo.

Проверить через API:

```bash
curl -s -u admin:admin http://127.0.0.1:3000/api/datasources \
  | jq -r '.[] | [.name,.type,.url,.isDefault] | @tsv'
```

## Как приложениям отправлять трейсы

Приложения должны отправлять OTLP в OpenTelemetry Collector:

```text
observability-otel-opentelemetry-collector.observability.svc.cluster.local:4317
```

Для HTTP OTLP:

```text
http://observability-otel-opentelemetry-collector.observability.svc.cluster.local:4318
```

Collector отправляет трейсы в Tempo, а OTLP-метрики публикует на `/metrics`,
откуда их забирает Prometheus.

## Важные ограничения локального стенда

- Persistence выключен, поэтому данные пропадут после пересоздания pod'ов.
- Retention сделан коротким: 24 часа.
- Alertmanager пока не отправляет уведомления наружу.
- Для production нужно включить persistent volumes, HA-реплики и внешние каналы алертов.
