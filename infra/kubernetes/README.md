# Локальная Kubernetes-инфраструктура

Этот файл описывает, как поднять локальный Kubernetes-кластер для проекта
NoteFlow.

Для задания используется отдельный профиль Minikube `noteflow-cilium`.

## 1.1 Кластер Minikube с Cilium

Cilium используется как CNI-плагин. Он отвечает за сеть между pod'ами, сетевые
политики и eBPF-наблюдаемость.

Команда запуска:

```bash
minikube start \
  -p noteflow-cilium \
  --driver=docker \
  --nodes=2 \
  --cni=cilium \
  --addons=metrics-server \
  --cpus=2 \
  --memory=4096
```

Переключиться на кластер:

```bash
kubectl config use-context noteflow-cilium
```

Проверить, что кластер работает:

```bash
kubectl get nodes -o wide
kubectl get pods -n kube-system
kubectl top nodes
```

Проверить Cilium:

```bash
kubectl get pods -n kube-system -l k8s-app=cilium
kubectl exec -n kube-system ds/cilium -- cilium status
```

Текущее состояние после настройки:

- профиль Minikube: `noteflow-cilium`
- Kubernetes: `v1.34.0`
- Cilium: `v1.18.1`
- ноды: `noteflow-cilium`, `noteflow-cilium-m02`
- `metrics-server` установлен и отдает метрики

## 1.2 Cluster Autoscaler

В задании нужно установить Karpenter или Cluster Autoscaler для автоматического
масштабирования worker-нод.

Для локального Minikube есть важное ограничение: Minikube с Docker-драйвером не
умеет автоматически создавать новые настоящие worker-ноды под нагрузкой, как это
делают облачные кластеры в AWS, GCP или Azure.

Поэтому для локальной проверки используется Cluster Autoscaler с `kwok` provider.
Он показывает работу autoscaler и создает виртуальные Kubernetes-ноды. Это
подходит для демонстрации логики scale-out, но не заменяет настоящий облачный
node group.

Установка:

```bash
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm upgrade --install cluster-autoscaler autoscaler/cluster-autoscaler \
  --version 9.53.0 \
  --namespace kube-system \
  -f infra/kubernetes/cluster-autoscaler-values.yaml
```

Проверить установку:

```bash
kubectl get deploy -n kube-system cluster-autoscaler-kwok-cluster-autoscaler
kubectl logs -n kube-system deploy/cluster-autoscaler-kwok-cluster-autoscaler --tail=120
```

## Проверка масштабирования

Создаем тестовую нагрузку:

```bash
kubectl create namespace ca-test
kubectl create deployment scale-test \
  --image=registry.k8s.io/pause:3.10 \
  --replicas=8 \
  -n ca-test
```

Добавляем настройки, из-за которых pod'ы должны попасть на виртуальную группу
нод `kind-worker`:

```bash
kubectl patch deployment scale-test -n ca-test --type=json \
  -p='[
    {"op":"add","path":"/spec/template/spec/nodeSelector","value":{"kwok-nodegroup":"kind-worker"}},
    {"op":"add","path":"/spec/template/spec/tolerations","value":[{"key":"kwok-provider","operator":"Equal","value":"true","effect":"NoSchedule"}]},
    {"op":"add","path":"/spec/template/spec/containers/0/resources","value":{"requests":{"cpu":"500m","memory":"128Mi"}}}
  ]'
```

Проверить результат:

```bash
kubectl get nodes --show-labels
kubectl logs -n kube-system deploy/cluster-autoscaler-kwok-cluster-autoscaler --tail=160
```

В логах должны появиться строки:

- `TriggeredScaleUp`
- `ScaledUpGroup`
- `kind-worker 0->1`

После проверки можно удалить тестовые ресурсы:

```bash
kubectl delete namespace ca-test
```

Если появилась виртуальная KWOK-нода, ее тоже можно удалить:

```bash
kubectl delete node <node-name>
```

