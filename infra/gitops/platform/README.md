# Платформенный слой Kubernetes

Эта папка содержит GitOps-манифесты для ядра трафика NoteFlow.

## Service Mesh

Папка: `service-mesh`

Что настроено:

- namespace `noteflow` с `istio-injection=enabled`
- `PeerAuthentication` для mTLS в режиме `PERMISSIVE`
- `DestinationRule` для трех сервисов:
  - `user-service`
  - `note-service`
  - `file-service`
- circuit breaker через `outlierDetection`
- connection pool limits
- retry-политики через `VirtualService`

Проверка:

```bash
kubectl get gateway,virtualservice,destinationrule,peerauthentication -n noteflow
```

## Ingress / API Gateway

Папка: `ingress`

Что настроено:

- Istio `Gateway` `noteflow-gateway`
- `VirtualService` для маршрутизации:
  - `/auth`, `/users` -> `user-service`
  - `/notes`, `/tags`, `/search` -> `note-service`
  - `/files` -> `file-service`
- HAProxy edge layer:
  - `Deployment` на 2 реплики
  - `Service` типа `NodePort`
  - порт `30080`

Проверка:

```bash
kubectl get pods -n edge
kubectl get svc -n edge
kubectl get gateway,virtualservice -n noteflow
```

Локальный доступ через Minikube:

```bash
minikube -p noteflow-cilium ip
curl -i http://$(minikube -p noteflow-cilium ip):30080/health/user
```

Пока сами микросервисы не развернуты в Kubernetes, gateway может отвечать `503`.
Это нормально: входная точка есть, но backend-сервисов еще нет.

## Rate Limiting

Папка: `rate-limit`

Что настроено:

- Valkey как Redis-совместимый backend
- Envoy Rate Limit Service
- `EnvoyFilter`, который подключает rate limiting к Istio ingress gateway

Лимиты:

- общий лимит: `100` запросов в минуту
- `/auth/login`: `5` запросов в минуту
- `/auth/register`: `10` запросов в час
- `/files`: `30` запросов в минуту

Проверка:

```bash
kubectl get pods -n rate-limit
kubectl get svc -n rate-limit
kubectl get envoyfilter -n istio-system
kubectl logs -n rate-limit deploy/ratelimit
```

## Keepalived

Keepalived-конфиги лежат отдельно в `infra/keepalived`.

В локальном Minikube на macOS VRRP/VIP полноценно не проверяется, потому что для
этого нужна L2-сеть и Linux edge-ноды. Поэтому локально используется HAProxy
через NodePort, а Keepalived описан как production-вариант для двух edge-нод.

## Observability

Папка: `observability`

Что настроено:

- `PrometheusRule` с базовыми алертами для pod'ов, нод, Istio и rate-limit;
- `ServiceMonitor` для `istiod`, Loki, Tempo, OpenTelemetry Collector и Rate Limit Service;
- `PodMonitor` для Istio ingress gateway.

Подробное описание стека, вариантов и команд проверки лежит в `infra/observability/README.md`.
