#!/usr/bin/env python
"""Точка входа для запуска сайта.

    python run.py            # локальная разработка (http://127.0.0.1:5000)
    gunicorn -w 4 'app:create_app()'   # продакшен
"""
from __future__ import annotations

import os
import secrets

from app import create_app
from app.config import Config


def _ensure_admin_password() -> None:
    """Генерирует пароль администратора при первом запуске, если его нет."""
    if Config.ADMIN_PASSWORD:
        return
    path = Config.DATA_DIR / "admin_secret.txt"
    if path.is_file():
        return
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(12)
    path.write_text(password, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    print("=" * 66)
    print(" Сгенерирован пароль администратора:", password)
    print(" Сохраните его в .env как ADMIN_PASSWORD=... и удалите data/admin_secret.txt")
    print("=" * 66)


_ensure_admin_password()
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    debug = os.environ.get("APP_ENV", "development") == "development"
    print(f"Сайт: http://{host}:{port}  |  Админка: http://{host}:{port}/admin/login")
    app.run(host=host, port=port, debug=debug, threaded=True)
