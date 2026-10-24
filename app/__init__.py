"""Фабрика приложения Flask."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, redirect, render_template, request
from werkzeug.exceptions import HTTPException

from . import security
from .config import get_config

__all__ = ["create_app"]


def _setup_logging(app: Flask) -> logging.Logger:
    log_dir = Path(app.config["LOG_DIR"])
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = app.logger
    logger.setLevel(logging.INFO)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:  # pragma: no cover
            pass

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"
    )

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    access = RotatingFileHandler(
        log_dir / "access.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    access.setFormatter(fmt)
    access.setLevel(logging.INFO)
    logger.addHandler(access)

    errors = RotatingFileHandler(
        log_dir / "errors.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    errors.setFormatter(fmt)
    errors.setLevel(logging.WARNING)
    logger.addHandler(errors)

    return logger


def create_app(config: object | None = None) -> Flask:
    """Создаёт приложение.

    config — класс конфигурации или объект с атрибутами (для тестов).
    """
    if config is None:
        config_class = get_config()
    elif isinstance(config, str):
        config_class = get_config()
    else:
        config_class = config
    app = Flask(
        __name__,
        instance_relative_config=False,
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_object(config_class)
    app.config.update(
        MAX_CONTENT_LENGTH=app.config["MAX_CONTENT_LENGTH"],
        JSON_AS_ASCII=False,
        SEND_FILE_MAX_AGE_DEFAULT=60 * 60 * 24 * 365,
        TEMPLATES_AUTO_RELOAD=app.config.get("DEBUG", False),
        TRAP_HTTP_EXCEPTIONS=False,
    )

    logger = _setup_logging(app)

    secret_path = Path(app.config["DATA_DIR"]) / "admin_secret.txt"
    if not app.config.get("ADMIN_PASSWORD") and not secret_path.is_file():
        logger.warning(
            "ADMIN_PASSWORD не задан и %s отсутствует — вход в админ-панель "
            "заблокирован. Запустите python run.py или задайте ADMIN_PASSWORD в .env",
            secret_path,
        )

    # --- Шаблоны и глобальные функции ---------------------------------
    app.jinja_env.globals.update(
        jsonld_block=security.jsonld_block,
        csrf_token=security.generate_csrf_token,
        current_year=security.current_year,
        plural_forms=security.plural_forms,
        site_name=app.config["SITE_NAME"],
        site_domain=app.config["SITE_DOMAIN"],
        base_url=app.config["BASE_URL"],
        telegram_username=app.config["TELEGRAM_USERNAME"],
        telegram_display=app.config["TELEGRAM_DISPLAY"],
        email=app.config["EMAIL"],
        github_url=app.config["GITHUB_URL"],
    )

    @app.context_processor
    def inject_globals() -> dict:
        canonical = app.config["BASE_URL"].rstrip("/") + request.path
        return {
            "canonical_url": canonical,
            "current_path": request.path,
            "site_name": app.config["SITE_NAME"],
            "telegram_username": app.config["TELEGRAM_USERNAME"],
            "telegram_display": app.config["TELEGRAM_DISPLAY"],
            "email": app.config["EMAIL"],
            "github_url": app.config["GITHUB_URL"],
            "base_url": app.config["BASE_URL"],
        }

    # --- Редиректы и безопасность --------------------------------------
    @app.before_request
    def enforce_scheme_and_host():
        host = (request.host or "").split(":")[0].lower()
        if app.config["FORCE_WWW_REDIRECT"] and host.startswith("www."):
            target = request.url.replace("//www.", "//", 1)
            return redirect(target, code=301)
        if app.config["FORCE_HTTPS"] and not security.wants_https():
            target = request.url.replace("http://", "https://", 1)
            return redirect(target, code=301)
        return None

    @app.after_request
    def finalize(response):
        response = security.apply_security_headers(response)
        if request.path.startswith("/static/"):
            response.headers.setdefault(
                "Cache-Control", "public, max-age=31536000, immutable"
            )
        else:
            response.headers.setdefault("Cache-Control", "public, max-age=0, must-revalidate")
        if response.status_code >= 400:
            logger.warning(
                "%s %s -> %s | ip=%s ua=%s",
                request.method,
                request.full_path.rstrip("?"),
                response.status_code,
                security.client_ip(),
                request.user_agent.string[:200],
            )
        return response

    # --- Обработка ошибок ---------------------------------------------
    def _render_error(code: int, message: str):
        try:
            return render_template(f"error.html", code=code, message=message), code
        except Exception:  # pragma: no cover - подстраховка
            return f"{code} {message}", code

    @app.errorhandler(404)
    def handle_404(error):
        if request.path.startswith("/api/"):
            return {"error": "not_found"}, 404
        return render_template("404.html"), 404

    _HTTP_MESSAGES = {
        400: "Некорректный запрос",
        401: "Требуется авторизация",
        403: "Доступ запрещён",
        405: "Метод не поддерживается",
        413: "Слишком большой запрос",
        429: "Слишком много запросов. Попробуйте позже.",
        500: "Внутренняя ошибка сервера",
    }

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        code = error.code or 500
        if request.path.startswith("/api/"):
            return {"ok": False, "message": _HTTP_MESSAGES.get(code, error.description)}, code
        return _render_error(code, _HTTP_MESSAGES.get(code, error.description))

    @app.errorhandler(500)
    def handle_500(error):
        logger.exception("Внутренняя ошибка на %s", request.path)
        return _render_error(500, _HTTP_MESSAGES[500])

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        if isinstance(error, HTTPException):
            return handle_http_error(error)
        logger.exception("Необработанная ошибка на %s", request.path)
        return _render_error(500, _HTTP_MESSAGES[500])

    # --- Маршруты -------------------------------------------------------
    from .admin import admin_bp
    from .views import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
