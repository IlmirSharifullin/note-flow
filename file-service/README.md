# File Service

Отвечает за загрузку, хранение и выдачу файлов и изображений. Файлы стримятся в MinIO (S3-совместимое хранилище), метаданные хранятся в PostgreSQL.

## Стек

- **FastAPI** + **SQLAlchemy (async)** + **asyncpg**
- **PostgreSQL** — метаданные файлов
- **MinIO** — хранение файлов (S3-совместимое API)
- **aiobotocore** — async AWS/S3 клиент
- **Apache Kafka** — публикация и потребление событий

## API

| Метод | Маршрут | Описание |
|---|---|---|
| POST | `/files` | Загрузить файл (multipart, max 100 МБ) |
| GET | `/files` | Список файлов пользователя |
| GET | `/files/{id}/url` | Presigned URL для скачивания (TTL 1 ч) |
| GET | `/files/{id}/meta` | Метаданные файла |
| DELETE | `/files/{id}` | Мягкое удаление |

## Хранение

Файлы распределяются по бакетам MinIO в зависимости от времени последнего обращения:

| Бакет | Критерий |
|---|---|
| `noteflow-hot` | Активные файлы (0–90 дней) |
| `noteflow-warm` | Без обращений 90–365 дней |

## Kafka события

Публикует в `file.events`: `file.uploaded`, `file.deleted`

Потребляет:
- `user.deleted` → удаляет все файлы пользователя из MinIO и помечает в БД

## Запуск

```bash
uv sync
uvicorn app.main:app --reload --port 8003
```
