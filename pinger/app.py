import json
import logging
import os
import sys
import time
from pathlib import Path

import psycopg

DEFAULT_INTERVAL_SECONDS = 300  # 5 минут
CONNECT_TIMEOUT_SECONDS = 5
STATEMENT_TIMEOUT_MS = 5000


def setup_logging() -> logging.Logger:
    """Настраивает логгер: INFO -> stdout, ERROR и выше -> stderr,
    и, если задан LOG_FILE_PATH, дублирует всё в файл."""
    logger = logging.getLogger("pinger")
    if logger.handlers:
        # Логгер уже настроен (защита от повторной настройки в одном процессе)
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    log_file_path = os.environ.get("LOG_FILE_PATH")
    if log_file_path:
        try:
            Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError as error:
            # Не удалось открыть файл лога - не критично, продолжаем работу
            # только с выводом в stdout/stderr.
            logger.error("Не удалось открыть файл логов %s: %s", log_file_path, error)

    return logger


def load_config(logger: logging.Logger, path: str = "config.json") -> dict:
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        logger.error("Не удалось прочитать конфиг %s: %s", path, error)
        sys.exit(1)


def get_env_int(name: str, default: int, logger: logging.Logger) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.error(
            "Некорректное значение переменной %s=%r, используется значение по умолчанию %s",
            name, value, default,
        )
        return default


def check_db_version(connection_params: dict, logger: logging.Logger) -> None:
    """Одна проверка БД. Любая ошибка здесь перехватывается и логируется,
    цикл в main() продолжает работу дальше по расписанию."""
    try:
        with psycopg.connect(**connection_params) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                result = cursor.fetchone()

        version_string = result[0] if result else None

        if version_string and "PostgreSQL" in version_string:
            logger.info("Подключение успешно. Версия БД: %s", version_string)
        else:
            # Ответ получен без ошибки, но выглядит нетипично
            logger.info("Подключение успешно, но ответ на запрос версии нетипичный: %r", version_string)

    except Exception as error:
        logger.error("Ошибка подключения к БД: %s", error)


def main() -> None:
    logger = setup_logging()
    config = load_config(logger)

    username = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")

    if not username or not password:
        logger.error("Не заданы переменные окружения DB_USER и/или DB_PASSWORD")
        sys.exit(1)

    interval_seconds = get_env_int("CHECK_INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS, logger)

    connection_params = {
        "host": config["host"],
        "port": config["port"],
        "dbname": config["database"],
        "user": username,
        "password": password,
        "connect_timeout": CONNECT_TIMEOUT_SECONDS,
        "options": f"-c statement_timeout={STATEMENT_TIMEOUT_MS}",
    }

    logger.info(
        "Сервис проверки БД запущен. Хост: %s:%s, БД: %s, интервал: %s сек.",
        config["host"], config["port"], config["database"], interval_seconds,
    )

    try:
        while True:
            check_db_version(connection_params, logger)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("Остановка сервиса по сигналу пользователя.")


if __name__ == "__main__":
    main()
