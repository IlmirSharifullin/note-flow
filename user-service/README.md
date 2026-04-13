# User Service

Отвечает за регистрацию, аутентификацию и управление профилем пользователя. Access токены — JWT (HS256), refresh токены хранятся в Redis.

## Стек

- **FastAPI** + **SQLAlchemy (async)** + **asyncpg**
- **PostgreSQL** — пользователи
- **Redis** — JWT blacklist, refresh токены, кэш профиля
- **Apache Kafka** — публикация событий

## API

| Метод | Маршрут | Описание |
|---|---|---|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/login` | Вход (access + refresh токен) |
| POST | `/auth/refresh` | Обновить access токен (httpOnly cookie) |
| POST | `/auth/logout` | Выход (инвалидация токенов) |
| GET | `/users/me` | Профиль текущего пользователя |
| PATCH | `/users/me` | Обновить профиль |
| DELETE | `/users/me` | Удалить аккаунт |

## Токены

- **Access token** — JWT, TTL 15 минут, передаётся в заголовке `Authorization: Bearer`
- **Refresh token** — хранится в Redis (`refresh:{hash}`), TTL 30 дней, передаётся в httpOnly cookie по пути `/auth/refresh`
- При удалении аккаунта все сессии отзываются через `sessions:{user_id}`

## Kafka события

Публикует в `user.events`: `user.registered`, `user.deleted`

## Запуск

```bash
uv sync
uvicorn app.main:app --reload --port 8001
```
