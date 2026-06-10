# GitOps через ArgoCD

В этой папке лежит конфигурация для ArgoCD.

Используется паттерн **App of Apps**:

- `root-app.yaml` создает главное приложение `noteflow-root`
- `noteflow-root` читает папку `infra/gitops/apps`
- в папке `apps` лежат дочерние ArgoCD Applications
- дочерние Applications уже разворачивают конкретные части инфраструктуры

Сейчас добавлено дочернее приложение `kafka-platform`. Оно синхронизирует
манифесты Kafka из папки `infra/gitops/platform/kafka`.

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
