"""Админ-панель: вход, управление кейсами («Скрыть кейс»), заявки."""
from __future__ import annotations

import hmac
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from . import content, security, storage

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_password() -> str:
    """Пароль администратора: из переменной окружения или из data/admin_secret.txt."""
    configured = current_app.config.get("ADMIN_PASSWORD")
    if configured:
        return configured
    path = Path(current_app.config["DATA_DIR"]) / "admin_secret.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return ""


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_auth"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@admin_bp.after_request
def noindex(response):
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_auth"):
        return redirect(url_for("admin.dashboard"))

    attempt_key = f"admin-login:{security.client_ip()}"
    error = None
    if request.method == "POST":
        if security.rate_limit_exceeded(attempt_key):
            current_app.logger.warning(
                "Слишком много попыток входа в админ-панель | ip=%s", security.client_ip()
            )
            return (
                render_template(
                    "admin/login.html",
                    error="Слишком много попыток. Попробуйте через 10 минут.",
                ),
                429,
            )
        if not security.check_csrf_token(request.form.get("csrf_token", "")):
            error = "Сессия устарела. Обновите страницу."
        else:
            submitted = request.form.get("password", "")
            expected = admin_password()
            if expected and hmac.compare_digest(submitted, expected):
                security.reset_rate_limit(attempt_key)
                session.clear()
                session["admin_auth"] = True
                session.permanent = True
                current_app.logger.info("Успешный вход в админ-панель")
                target = request.args.get("next") or url_for("admin.dashboard")
                if not target.startswith("/admin"):
                    target = url_for("admin.dashboard")
                return redirect(target)
            current_app.logger.warning("Неудачная попытка входа в админ-панель")
            error = "Неверный пароль"

    return render_template("admin/login.html", error=error), (401 if error else 200)


@admin_bp.post("/logout")
@login_required
def logout():
    if not security.check_csrf_token(request.form.get("csrf_token", "")):
        abort(400)
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.get("/")
@login_required
def dashboard():
    state = storage.load_case_state()
    rows = []
    for case in content.CASES:
        item = state.get(case.slug)
        hidden = case.hidden
        if isinstance(item, dict) and "hidden" in item:
            hidden = bool(item["hidden"])
        rows.append(
            {
                "slug": case.slug,
                "title": case.title,
                "category": case.category,
                "year": case.year,
                "featured": case.featured,
                "hidden": hidden,
                "updated_at": item.get("updated_at") if isinstance(item, dict) else None,
            }
        )
    return render_template(
        "admin/dashboard.html",
        rows=rows,
        messages=storage.list_messages(100),
        new_count=storage.count_new_messages(),
    )


@admin_bp.post("/cases/<slug>/toggle")
@login_required
def toggle_case(slug: str):
    if not security.check_csrf_token(request.form.get("csrf_token", "")):
        abort(400)
    if content.get_case(slug) is None:
        abort(404)
    hidden = "1" in request.form.getlist("hidden")
    storage.set_case_hidden(slug, hidden)
    flash(
        f"Кейс «{content.get_case(slug).title}» {'скрыт' if hidden else 'опубликован'}.",
        "success",
    )
    return redirect(url_for("admin.dashboard") + "#cases")


@admin_bp.post("/messages/<int:message_id>/status")
@login_required
def message_status(message_id: int):
    if not security.check_csrf_token(request.form.get("csrf_token", "")):
        abort(400)
    status = request.form.get("status", "new")
    if status not in {"new", "done", "archived"}:
        abort(400)
    storage.set_message_status(message_id, status)
    return redirect(url_for("admin.dashboard") + "#messages")


@admin_bp.post("/messages/<int:message_id>/delete")
@login_required
def message_delete(message_id: int):
    if not security.check_csrf_token(request.form.get("csrf_token", "")):
        abort(400)
    storage.delete_message(message_id)
    flash("Заявка удалена.", "success")
    return redirect(url_for("admin.dashboard") + "#messages")


@admin_bp.get("/secret")
@login_required
def show_secret():
    """Показывает сгенерированный пароль, чтобы его можно было заменить в .env."""
    path = Path(current_app.config["DATA_DIR"]) / "admin_secret.txt"
    secret = path.read_text(encoding="utf-8").strip() if path.is_file() else ""
    return render_template("admin/secret.html", secret=secret)
