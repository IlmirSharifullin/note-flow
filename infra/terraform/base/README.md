# Terraform: базовая инфраструктура Kubernetes

Этот модуль описывает минимальную инфраструктуру внутри уже созданного
Kubernetes-кластера:

- namespaces: `argocd`, `noteflow`, `kafka`, `monitoring`
- service accounts для деплоя и приложений
- базовые Kubernetes Secrets для NoteFlow и Kafka

Terraform читает доступ к кластеру из локального kubeconfig.

## Подготовка

```bash
kubectl config use-context noteflow-cilium
cp terraform.tfvars.example terraform.tfvars
```

После этого нужно заполнить значения в `terraform.tfvars`.

## Применение

```bash
terraform init
terraform plan
terraform apply
```

Важно: значения секретов попадут в Terraform state. Для учебного локального
кластера это нормально, но для настоящего окружения лучше использовать External
Secrets, Vault или SOPS.
