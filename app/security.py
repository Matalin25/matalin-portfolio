"""Безопасность: заголовки, CSP, санитизация, валидация, CSRF, rate limit.

Все входящие данные проходят двойную проверку (клиент + сервер), очищаются от
HTML-тегов и спецсимволов, а формы защищены honeypot-полем и CSRF-токеном.
"""
from __future__ import annotations

import base64
import hashlib
import re
import secrets
import time
import unicodedata
from collections import defaultdict, deque
from typing import Any, Iterable

from flask import current_app, g, has_request_context, request, session
from markupsafe import Markup

# ---------------------------------------------------------------------------
# CSP
# ---------------------------------------------------------------------------

# Хэши инлайновых <script type="application/ld+json"> вычисляются на лету,
# поэтому в политике нет 'unsafe-inline' для скриптов.
_CSP_TEMPLATE = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'self'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "style-src 'self'; "
    "script-src 'self' {hashes}; "
    "form-action 'self'; "
    "frame-src 'none'; "
    "media-src 'self'"
)


def register_jsonld_hash(payload: str) -> None:
    """Запоминает хэш инлайнового JSON-LD блока для CSP."""
    digest = base64.b64encode(hashlib.sha256(payload.encode("utf-8")).digest()).decode("ascii")
    hashes = getattr(g, "_csp_hashes", None)
    if hashes is None:
        hashes = []
        g._csp_hashes = hashes
    if digest not in hashes:
        hashes.append(digest)


def jsonld_block(payload: str) -> Markup:
    """Оборачивает JSON-LD в <script> и добавляет его хэш в CSP."""
    safe = payload.replace("<", "\\u003c").replace(">", "\\u003e")
    register_jsonld_hash(safe)
    return Markup(f'<script type="application/ld+json">{safe}</script>')


def build_csp() -> str:
    hashes = getattr(g, "_csp_hashes", []) or []
    hash_list = " ".join(f"'sha256-{h}'" for h in hashes)
    policy = _CSP_TEMPLATE.format(hashes=hash_list).strip()
    if current_app.config.get("FORCE_HTTPS"):
        policy += "; upgrade-insecure-requests"
    return policy


# ---------------------------------------------------------------------------
# Заголовки безопасности
# ---------------------------------------------------------------------------

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "accelerometer=(), autoplay=(), camera=(), display-capture=(), "
        "encrypted-media=(), fullscreen=(self), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), midi=(), payment=(), "
        "picture-in-picture=(), publickey-credentials-get=(), screen-wake-lock=(), "
        "usb=(), xr-spatial-tracking=()"
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-XSS-Protection": "0",
}


def apply_security_headers(response):
    """Добавляет заголовки безопасности ко всем ответам."""
    response.headers.setdefault("Content-Security-Policy", build_csp())
    for key, value in SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    if current_app.config.get("FORCE_HTTPS"):
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload"
        )
    response.headers.setdefault("X-Robots-Tag", "index, follow")
    return response


def wants_https() -> bool:
    if request.is_secure:
        return True
    if current_app.config.get("TRUST_PROXY_SSL"):
        proto = request.headers.get("X-Forwarded-Proto", "")
        return proto.split(",")[0].strip().lower() == "https"
    return False


def is_www_host() -> bool:
    host = (request.host or "").split(":")[0].lower()
    return host.startswith("www.")


# ---------------------------------------------------------------------------
# Санитизация и валидация
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(r"<[^>]*>")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_UNSAFE_RE = re.compile(r"[<>\"'`\\]")
_WHITESPACE_RE = re.compile(r"\s+")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def sanitize_text(value: Any, max_length: int = 1000) -> str:
    """Убирает HTML-теги, управляющие символы и опасные спецсимволы."""
    if value is None:
        return ""
    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = _TAG_RE.sub(" ", text)
    text = _CONTROL_RE.sub("", text)
    text = text.replace("<", "").replace(">", "")
    text = _UNSAFE_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if len(text) > max_length:
        text = text[: max_length - 1].rstrip() + "…"
    return text


def sanitize_multiline(value: Any, max_length: int = 2000) -> str:
    """Санитизация многострочного текста (сохраняет переносы строк)."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = _TAG_RE.sub(" ", text)
    text = _CONTROL_RE.sub("", text)
    text = text.replace("<", "").replace(">", "")
    text = _UNSAFE_RE.sub("", text)
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    result = "\n".join(line for line in lines if line)
    if len(result) > max_length:
        result = result[: max_length - 1].rstrip() + "…"
    return result


def is_valid_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value or "")) and len(value) <= 120


def is_valid_slug(value: str) -> bool:
    return bool(_SLUG_RE.match(value or "")) and len(value) <= 80


def validate_contact(payload: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    """Серверная валидация формы обратной связи.

    Возвращает (очищенные данные, список ошибок).
    """
    cfg = current_app.config
    name = sanitize_text(payload.get("name"), cfg["MAX_CONTENT_LENGTH_NAME"])
    contact = sanitize_text(payload.get("contact"), cfg["MAX_CONTENT_LENGTH_EMAIL"])
    message = sanitize_multiline(payload.get("message"), cfg["MAX_CONTENT_LENGTH_MESSAGE"])
    consent = payload.get("consent")
    honeypot = sanitize_text(payload.get("website"), 100)

    errors: list[str] = []
    if not name:
        errors.append("Укажите, как к вам обращаться")
    elif len(name) < 2:
        errors.append("Имя слишком короткое")
    if not contact:
        errors.append("Укажите Telegram или email для ответа")
    elif "@" in contact:
        if not is_valid_email(contact):
            errors.append("Проверьте формат email")
    else:
        if not _USERNAME_RE.match(contact.lstrip("@")):
            errors.append("Проверьте ник в Telegram")
    if len(message) < 10:
        errors.append("Опишите задачу подробнее — минимум 10 символов")
    if not consent:
        errors.append("Подтвердите согласие на обработку персональных данных")

    return {"name": name, "contact": contact, "message": message}, errors


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------

CSRF_FIELD = "csrf_token"


def generate_csrf_token() -> str:
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token


def check_csrf_token(token: str) -> bool:
    expected = session.get("_csrf") or ""
    if not expected or not token:
        return False
    return secrets.compare_digest(str(expected), str(token))


# ---------------------------------------------------------------------------
# Rate limit (в памяти процесса)
# ---------------------------------------------------------------------------

_hits: dict[str, deque[float]] = defaultdict(deque)


def client_ip() -> str:
    if not has_request_context():
        return "unknown"
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded and current_app.config.get("TRUST_PROXY_SSL"):
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limit_exceeded(key: str | None = None) -> bool:
    """Проверяет, не превышен ли лимит запросов для текущего клиента."""
    cfg = current_app.config
    bucket = key or client_ip()
    now = time.time()
    window = cfg["RATE_LIMIT_WINDOW"]
    limit = cfg["RATE_LIMIT_MAX"]
    queue = _hits[bucket]
    while queue and now - queue[0] > window:
        queue.popleft()
    if len(queue) >= limit:
        return True
    queue.append(now)
    return False


def reset_rate_limit(key: str | None = None) -> None:
    """Сбрасывает счётчик запросов (используется в тестах)."""
    if key is None:
        if not has_request_context():
            for queue in _hits.values():
                queue.clear()
            return
        key = client_ip()
    _hits[key].clear()


# ---------------------------------------------------------------------------
# Хелперы для шаблонов
# ---------------------------------------------------------------------------


def current_year() -> int:
    import datetime

    return datetime.date.today().year


def plural_forms(items: Iterable[Any]) -> str:
    """Русская склонка: 1 кейс / 2 кейса / 5 кейсов."""
    count = len(list(items))
    if count % 10 == 1 and count % 100 != 11:
        return "кейс"
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return "кейса"
    return "кейсов"
