# kafka_strimzi

Ansible role для установки Kafka в Kubernetes через Strimzi Operator.

Роль подходит для локального кластера Minikube и учебного окружения. Для
production нужно отдельно настроить storage class, ресурсы, TLS/SASL, backup и
мониторинг.

## Основные переменные

- `kafka_namespace`: namespace для Kafka
- `kafka_cluster_name`: имя Kafka-кластера
- `strimzi_install_url`: URL манифеста установки Strimzi
- `kafka_controller_replicas`: количество controller-нод
- `kafka_broker_replicas`: количество broker-нод
- `kafka_broker_storage_size`: размер PVC для broker-нод

Пример запуска:

```bash
ansible-playbook infra/ansible/playbooks/deploy-kafka.yml
```
