# Ansible для инфраструктуры

В этой папке лежит Ansible role для деплоя Kafka в Kubernetes через Strimzi.

Роль:

1. создает namespace `kafka`
2. устанавливает Strimzi Cluster Operator
3. применяет `KafkaNodePool`
4. применяет `Kafka`
5. ждет готовности Kafka-кластера

## Требования

Нужны:

- `ansible`
- доступный `kubectl` context
- Python-библиотека `kubernetes`
- коллекция `kubernetes.core`

Установка коллекции:

```bash
ansible-galaxy collection install -r requirements.yml
```

## Запуск

```bash
ansible-playbook playbooks/deploy-kafka.yml
```

По умолчанию Kafka ставится в namespace `kafka`, имя кластера:
`noteflow-kafka`.
