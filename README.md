# 1 ЗАДАНИЕ

## Запуск

```bash
docker compose up -d --build
```

## Проверка

```bash
docker ps
```

## Остановка

```bash
# Обычная остановка контейнеров
docker compose down
# Остановка с удалением volumes (чистка БД)
docker compose down -v
```

## Проверка существующих данных

```bash
docker volume ls
```

## Доступ

http://localhost:8080

## Подключение к PostgreSQL

| Параметр     | Значение         |
| ------------ | ---------------- |
| Система      | PostgreSQL       |
| Сервер       | `db`             |
| Пользователь | `postgres_admin` |
| Пароль       | `example`        |
| База данных  | `testdb`         |

## Создание пользователя и выдача прав

```sql
CREATE USER app_user WITH PASSWORD 'AppPassword123';
GRANT CONNECT ON DATABASE testdb TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
```

### Вывод списка пользователей

```sql
SELECT usename FROM pg_user;
```

```bash
python -m venv venv


.\venv\Scripts\activate

python -m pip install psycopg[binary]
```

установка `psycopg[binary]` падала при включённом VPN.

## Быстрая сводка команд

| Действие                    | Команда                        |
| --------------------------- | ------------------------------ |
| Запуск с пересборкой        | `docker compose up -d --build` |
| Список контейнеров          | `docker ps`                    |
| Остановка                   | `docker compose down`          |
| Остановка + чистка БД       | `docker compose down -v`       |
| Список volumes              | `docker volume ls`             |
| Создать venv                | `python -m venv venv`          |
| Активировать venv (Windows) | `.\venv\Scripts\activate`      |
| Установить psycopg          | `pip install psycopg[binary]`  |

# 2 ЗАДАНИЕ

cd rzps\_\_2

# 1. Собрать тегированный образ пингера

docker build -t db-pinger:1.0 ./pinger

# 2. Поднять всё (db соберётся из db/Dockerfile, pinger возьмёт готовый тег)

docker compose up -d --build

# 3. Проверить, что все 3 контейнера подняты

docker ps -a

# 4. Смотреть логи пингера

docker logs -f db_pinger
Ожидаемая картина в логах db_pinger: пока Postgres делает initdb (генерация ru_RU локали занимает время), первая-вторая проверка выдаст [ERROR] Ошибка подключения к БД: ..., а следующая через 15 секунд (CHECK_INTERVAL_SECONDS в pinger/.env) — [INFO] Подключение успешно. Версия БД: PostgreSQL 18.... Это и есть демонстрация пункта 2.2 задания.

Чтобы показать сбой ещё раз в любой момент: docker stop postgres18, дождаться [ERROR] в логах, затем docker start postgres18 и дождаться [INFO].
