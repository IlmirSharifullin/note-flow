# GitOps через ArgoCD

В этой папке лежит конфигурация для ArgoCD.

Используется паттерн **App of Apps**:

- `root-app.yaml` создает главное приложение `noteflow-root`
- `noteflow-root` читает папку `infra/gitops/apps`
- в папке `apps` лежат дочерние ArgoCD Applications
- дочерние Applications уже разворачивают конкретные части инфраструктуры

Сейчас добавлены дочерние приложения:

- `kafka-platform` - Kafka через Strimzi;
- `service-mesh-platform` - Istio service mesh настройки;
- `ingress-platform` - Istio Gateway и HAProxy edge layer;
- `rate-limit-platform` - Envoy Rate Limit Service и Valkey;
- `local-registry` - локальный Docker Registry для CI/CD;
- `noteflow-services` - Helm chart трех микросервисов;
- `observability-*` - Prometheus, Grafana, Loki, Tempo и OpenTelemetry Collector.

## Установка ArgoCD

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  -f infra/gitops/argocd/values.yaml
```

## Создание root application

```bash
kubectl apply -f infra/gitops/root-app.yaml
```

## Проверка

```bash
kubectl get pods -n argocd
kubectl get applications -n argocd
```

Важно: ArgoCD синхронизируется из Git-репозитория
`https://github.com/IlmirSharifullin/note-flow`. Новые локальные файлы начнут
синхронизироваться только после commit и push.
