"""Конфигурация приложения.

Все чувствительные значения читаются из переменных окружения (.env),
поэтому секреты не попадают в репозиторий.
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"


def _load_dotenv() -> None:
    """Минимальный загрузчик .env (без внешних зависимостей)."""
    env_path = BASE_DIR / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()

DATA_DIR = Path(os.environ.get("DATA_DIR") or BASE_DIR / "data")
LOG_DIR = Path(os.environ.get("LOG_DIR") or BASE_DIR / "logs")
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR") or BASE_DIR / "backups")
SECRET_FILE = DATA_DIR / "secret_key.txt"


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _secret_key() -> str:
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SECRET_FILE.is_file():
        return SECRET_FILE.read_text(encoding="utf-8").strip()
    generated = secrets.token_hex(32)
    SECRET_FILE.write_text(generated, encoding="utf-8")
    try:
        os.chmod(SECRET_FILE, 0o600)
    except OSError:
        pass
    return generated


class Config:
    """Базовая конфигурация."""

    # --- Сайт -----------------------------------------------------------
    SITE_NAME = "Маталин"  # TODO: замените на Имя Фамилию владельца
    SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "matalin-portfolio.ru")
    BASE_URL = os.environ.get("BASE_URL", f"https://{SITE_DOMAIN}").rstrip("/")
    COMPANY_NAME = "Matalin Portfolio"

    # --- Контакты (TODO: замените на реальные) --------------------------
    TELEGRAM_USERNAME = os.environ.get("TELEGRAM_USERNAME", "matalin_dev")
    TELEGRAM_DISPLAY = os.environ.get("TELEGRAM_DISPLAY", "@matalin_dev")
    EMAIL = os.environ.get("EMAIL", "hello@matalin-portfolio.ru")
    GITHUB_URL = os.environ.get("GITHUB_URL", "https://github.com/matalin-dev")

    # --- Безопасность ---------------------------------------------------
    SECRET_KEY = _secret_key()
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    SESSION_COOKIE_NAME = "mp_admin"
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 часов
    MAX_CONTENT_LENGTH = 32 * 1024  # 32 КБ — ограничение размера тела запроса
    TRUST_PROXY_SSL = _env_bool("TRUST_PROXY_SSL", False)
    FORCE_HTTPS = _env_bool("FORCE_HTTPS", False)
    FORCE_WWW_REDIRECT = _env_bool("FORCE_WWW_REDIRECT", False)

    # --- Лимиты формы ---------------------------------------------------
    RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 600))  # сек
    RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", 5))  # заявок за окно

    # --- Прочее ----------------------------------------------------------
    MAX_CONTENT_LENGTH_NAME = 60
    MAX_CONTENT_LENGTH_EMAIL = 120
    MAX_CONTENT_LENGTH_MESSAGE = 2000
    ITEMS_PER_PAGE = 20

    # --- Telegram-уведомления (необязательно) ----------------------------
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

    # --- Хранилище -------------------------------------------------------
    DATA_DIR = DATA_DIR
    LOG_DIR = LOG_DIR
    BACKUP_DIR = BACKUP_DIR


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    FORCE_HTTPS = True
    FORCE_WWW_REDIRECT = True


class DevelopmentConfig(Config):
    DEBUG = True


def get_config() -> type[Config]:
    env = os.environ.get("APP_ENV", "development").lower()
    if env in {"production", "prod"}:
        return ProductionConfig
    if env == "development":
        return DevelopmentConfig
    return Config
