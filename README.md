# NoteFlow

Личный дневник и заметки в Markdown. Три независимых микросервиса на Python + FastAPI с асинхронным взаимодействием через Kafka.

## Сервисы

| Сервис | Порт | БД | Описание |
|---|---|---|---|
| [user-service](./user-service) | 8001 | PostgreSQL | Регистрация, аутентификация, JWT, профиль |
| [note-service](./note-service) | 8002 | MongoDB | Заметки, теги, история версий, поиск |
| [file-service](./file-service) | 8003 | PostgreSQL + MinIO | Загрузка файлов, presigned URL |

## Стек

- **Python 3.12** + **FastAPI** — все сервисы
- **PostgreSQL** — пользователи и метаданные файлов
- **MongoDB** — заметки (гибкая схема, full-text search)
- **Redis** — JWT blacklist, сессии, кэш
- **Apache Kafka** — асинхронные события между сервисами
- **MinIO** — S3-совместимое объектное хранилище для файлов
- **Docker Compose** — локальная разработка

## Быстрый старт

```bash
# Поднять инфраструктуру и все сервисы
docker compose up -d

# Swagger UI каждого сервиса
open http://localhost:8001/docs  # user-service
open http://localhost:8002/docs  # note-service
open http://localhost:8003/docs  # file-service
```

## Архитектура событий

```
user.registered  →  note-service (создаёт приветственную заметку)
user.deleted     →  note-service (soft-delete всех заметок)
                 →  file-service (удаляет файлы из MinIO)
file.uploaded    →  note-service (прикрепляет файл к заметке)
```

## Локальная разработка

Для разработки с hot-reload без пересборки образа — код монтируется как volume:

```bash
# Запустить только инфраструктуру
docker compose up -d postgres-users postgres-files mongo redis kafka minio

# Запустить сервис локально
cd user-service
uv sync
uvicorn app.main:app --reload --port 8001
```
