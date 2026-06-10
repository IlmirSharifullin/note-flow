# Istio

Istio установлен в локальный кластер через Helm.

Установленные releases:

- `istio-base` в namespace `istio-system`
- `istiod` в namespace `istio-system`
- `istio-ingressgateway` в namespace `istio-ingress`

Версия: `1.30.1`

Команды установки:

```bash
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

helm upgrade --install istio-base istio/base \
  --version 1.30.1 \
  --namespace istio-system \
  --create-namespace \
  --wait

helm upgrade --install istiod istio/istiod \
  --version 1.30.1 \
  --namespace istio-system \
  --wait

helm upgrade --install istio-ingressgateway istio/gateway \
  --version 1.30.1 \
  --namespace istio-ingress \
  --create-namespace \
  --set service.type=ClusterIP \
  --wait
```

Проверка:

```bash
kubectl get pods -n istio-system
kubectl get pods -n istio-ingress
kubectl get crd | grep istio.io
helm list -A
```
