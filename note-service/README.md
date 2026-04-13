# Note Service

Управляет заметками в формате Markdown: создание, редактирование, теги, история версий и полнотекстовый поиск. Все данные строго привязаны к пользователю.

## Стек

- **FastAPI** + **Beanie** (ODM) + **PyMongo async**
- **MongoDB** — заметки и история изменений
- **Redis** — кэш заметок и списков
- **Apache Kafka** — публикация и потребление событий

## API

| Метод | Маршрут | Описание |
|---|---|---|
| GET | `/notes` | Список заметок (пагинация, фильтр по тегу) |
| POST | `/notes` | Создать заметку |
| GET | `/notes/{id}` | Получить заметку |
| PATCH | `/notes/{id}` | Обновить заметку |
| DELETE | `/notes/{id}` | Soft delete |
| GET | `/notes/{id}/history` | История версий (последние 20) |
| GET | `/notes/trash` | Корзина (удалённые за 30 дней) |
| POST | `/notes/{id}/restore` | Восстановить из корзины |
| GET | `/tags` | Теги пользователя с количеством заметок |
| GET | `/search?q=` | Полнотекстовый поиск |

## Коллекции MongoDB

- `notes` — заметки с вложениями и тегами, soft delete через `deleted_at`
- `note_history` — снапшоты при каждом редактировании, TTL 30 дней, хранится до 20 ревизий

## Kafka события

Публикует в `note.events`: `note.created`, `note.updated`, `note.deleted`

Потребляет:
- `user.registered` → создаёт приветственную заметку
- `user.deleted` → soft-delete всех заметок пользователя
- `file.uploaded` → прикрепляет файл к заметке

## Запуск

```bash
uv sync
uvicorn app.main:app --reload --port 8002
```
