# CI/CD для NoteFlow через GitHub Actions

Эта часть описывает локальный pipeline:

1. GitHub Actions self-hosted runner запускает job'ы локально.
2. Kaniko собирает Docker images без Docker daemon.
3. Images пушатся в локальный registry Kubernetes.
4. Pipeline обновляет tag образов в Helm chart.
5. ArgoCD синхронизирует приложение в кластер.

## Локальный registry

Registry описан в GitOps:

- `infra/gitops/apps/local-registry.yaml`
- `infra/gitops/platform/local-registry`

Локально применить:

```bash
kubectl apply -f infra/gitops/platform/local-registry
```

Проверить:

```bash
kubectl get pods,svc -n registry
curl http://$(minikube -p noteflow-cilium ip):30500/v2/
```

Для Kubernetes pull используется ClusterIP registry:

```text
10.98.190.7:5000
```

Этот IP закреплен в `infra/gitops/platform/local-registry/registry.yaml`.
Minikube Docker daemon уже считает Service CIDR `10.96.0.0/12` insecure registry,
поэтому pull из HTTP registry работает без отдельной настройки TLS.

Проверка:

```bash
minikube -p noteflow-cilium ssh -- \
  'curl -s -o /tmp/registry-check.txt -w "%{http_code}\n" http://10.98.190.7:5000/v2/'
```

Smoke push:

```bash
minikube -p noteflow-cilium ssh -- \
  'docker tag registry:2 10.98.190.7:5000/noteflow/registry-smoke:latest && \
   docker push 10.98.190.7:5000/noteflow/registry-smoke:latest'
```

Workflow пушит images через временный `kubectl port-forward`:

```text
REGISTRY_PUSH_ENDPOINT=noteflow-github-runner:5000
```

Так сделано потому, что GitHub runner работает в Docker-контейнере, а Kaniko
запускается как соседний Docker-контейнер. Workflow открывает port-forward на
`0.0.0.0:5000`, подключает Kaniko к сети `github-runner_default` и пушит в
контейнер runner'а по имени `noteflow-github-runner`.

А в Helm chart записывает адрес, по которому image будет тянуть Kubernetes:

```text
REGISTRY_PULL_ENDPOINT=10.98.190.7:5000
```

## GitHub Actions self-hosted runner

Создать runner token в GitHub:

```text
Repository -> Settings -> Actions -> Runners -> New self-hosted runner
```

Скопировать `.env.example`:

```bash
cp infra/cicd/github-runner/.env.example infra/cicd/github-runner/.env
```

Заполнить `RUNNER_TOKEN`, затем запустить:

```bash
cd infra/cicd/github-runner
docker compose up -d
```

Runner получает labels:

```text
self-hosted, local, kaniko, noteflow
```

Именно эти labels использует workflow `.github/workflows/noteflow-cicd.yml`.

Runner container монтирует домашнюю папку read-only, чтобы внутри был доступен
тот же kubeconfig и minikube certificates. Это нужно для команды
`kubectl port-forward` внутри workflow.

## Secrets GitHub Actions

В репозитории добавить secrets:

- `ARGOCD_SERVER` - адрес ArgoCD API;
- `ARGOCD_AUTH_TOKEN` - token для ArgoCD;
- `ARGOCD_OPTS` - например `--insecure`, если ArgoCD без нормального TLS.

`GITHUB_TOKEN` используется автоматически для commit/push обновленного Helm values.

## Проверка pipeline

После push pipeline должен:

- собрать `user-service`, `note-service`, `file-service`;
- запушить images в локальный registry;
- заменить image tag в `infra/helm/noteflow-services/values.yaml`;
- сделать commit с `[ci skip]`;
- вызвать `argocd app sync noteflow-services`.

Проверить в Kubernetes:

```bash
kubectl get applications -n argocd
kubectl get pods -n noteflow
kubectl get svc -n noteflow
```
