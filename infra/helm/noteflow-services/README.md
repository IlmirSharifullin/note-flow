# Helm chart для микросервисов NoteFlow

Chart разворачивает три FastAPI-сервиса:

- `user-service`;
- `note-service`;
- `file-service`.

Для каждого сервиса создаются:

- `Deployment`;
- `Service`;
- общие `ConfigMap` и `Secret`.

## Подключения

Chart передает приложениям настройки:

- Kafka: `KAFKA_BOOTSTRAP_SERVERS`;
- Redis: `REDIS_URL`;
- MongoDB для `note-service`: `MONGODB_URL`, `MONGODB_DB`;
- PostgreSQL для `user-service` и `file-service`: `DATABASE_URL`;
- MinIO для `file-service`: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`;
- JWT secret: `JWT_SECRET`.

Значения по умолчанию лежат в `values.yaml`.

## Локальные зависимости

Для локального стенда chart также может поднять dev-зависимости:

- `postgres-users`;
- `postgres-files`;
- `mongo`;
- `redis`;
- `minio`.

Они включены флагом:

```yaml
devDependencies:
  enabled: true
```

Данные хранятся в `emptyDir`, то есть после пересоздания pod'ов они могут
пропасть. Для production этот блок нужно выключить и подключить внешние
managed-сервисы или отдельные Helm chart'ы с persistent volumes.

## Проверка шаблона

```bash
helm lint infra/helm/noteflow-services
helm template noteflow-services infra/helm/noteflow-services --namespace noteflow
```

## Важное про локальный registry

По умолчанию images указывают на:

```text
10.98.190.7:5000/noteflow/<service>
```

Это ClusterIP локального registry из `infra/gitops/platform/local-registry`.
Он находится внутри Service CIDR Minikube, который уже отмечен как insecure registry.
