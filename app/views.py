"""Публичные маршруты: главная, страница кейса, 404, sitemap, robots, форма."""
from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request
from datetime import date

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from . import content, security, seo, storage

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------------------
# Вспомогательное
# ---------------------------------------------------------------------------


def _public_cases() -> list[content.Case]:
    """Кейсы с учётом флагов «Скрыть кейс» из админ-панели."""
    state = storage.load_case_state()
    result = []
    for case in content.CASES:
        hidden = case.hidden
        item = state.get(case.slug)
        if isinstance(item, dict) and "hidden" in item:
            hidden = bool(item["hidden"])
        if hidden:
            continue
        result.append(case)
    return result


def _case_or_404(slug: str) -> content.Case:
    if not security.is_valid_slug(slug):
        abort(404)
    case = content.get_case(slug)
    if case is None:
        abort(404)
    state = storage.load_case_state().get(slug)
    hidden = case.hidden
    if isinstance(state, dict) and "hidden" in state:
        hidden = bool(state["hidden"])
    if hidden:
        # Скрытый кейс не должен попадать в индекс и не должен открываться по прямой ссылке.
        abort(404)
    return case



# ---------------------------------------------------------------------------
# Главная
# ---------------------------------------------------------------------------


@main_bp.route("/")
def index():
    cases = [c for c in _public_cases() if c.featured]
    hero = dict(content.HERO)
    hero["title"] = hero["title"].format(name=current_app.config["SITE_NAME"])
    return render_template(
        "index.html",
        hero=hero,
        about=content.ABOUT,
        contact=content.CONTACT,
        nav_links=content.NAV_LINKS,
        cases=cases,
        total_cases=len(_public_cases()),
        person_schema=seo.person_schema(),
        website_schema=seo.website_schema(),
    )


# ---------------------------------------------------------------------------
# Страница кейса
# ---------------------------------------------------------------------------


@main_bp.route("/projects/<slug>/")
@main_bp.route("/projects/<slug>")
def project(slug: str):
    case = _case_or_404(slug)
    others = [c for c in _public_cases() if c.slug != case.slug][:3]
    return render_template(
        "project.html",
        case=case,
        others=others,
        case_schema=seo.case_schema(case),
        person_schema=seo.person_schema(),
    )


@main_bp.route("/projects/")
def projects_index():
    return redirect(url_for("main.index") + "#cases", code=302)


# ---------------------------------------------------------------------------
# SEO
# ---------------------------------------------------------------------------


@main_bp.route("/sitemap.xml")
def sitemap():
    base = current_app.config["BASE_URL"]
    today = date.today().isoformat()
    urls: list[tuple[str, str, str]] = [(f"{base}/", "1.0", today)]
    for case in _public_cases():
        if case.featured:
            urls.append((f"{base}/projects/{case.slug}/", "0.8", today))
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, priority, lastmod in urls:
        body.append("  <url>")
        body.append(f"    <loc>{loc}</loc>")
        body.append(f"    <lastmod>{lastmod}</lastmod>")
        body.append(f"    <changefreq>monthly</changefreq>")
        body.append(f"    <priority>{priority}</priority>")
        body.append("  </url>")
    body.append("</urlset>")
    xml = "\n".join(body)
    return Response(xml, mimetype="application/xml")


@main_bp.route("/robots.txt")
def robots():
    base = current_app.config["BASE_URL"]
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin",
        "Disallow: /api/",
        "",
        f"Sitemap: {base}/sitemap.xml",
        "",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


# ---------------------------------------------------------------------------
# Форма обратной связи
# ---------------------------------------------------------------------------


def _notify_telegram(record: dict) -> bool:
    """Отправляет заявку в Telegram-чат, если заданы BOT_TOKEN и CHAT_ID."""
    token = current_app.config.get("TELEGRAM_BOT_TOKEN")
    chat_id = current_app.config.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    text = (
        f"Новая заявка с сайта\n"
        f"Имя: {record['name']}\n"
        f"Контакт: {record['contact']}\n"
        f"Сообщение: {record['message']}"
    )
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    request_obj = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=8) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, OSError, ValueError):
        current_app.logger.warning("Не удалось отправить заявку в Telegram", exc_info=True)
        return False


@main_bp.post("/api/contact")
def contact_submit():
    if not security.check_csrf_token(request.form.get("csrf_token", "")):
        return _contact_error("Сессия устарела. Обновите страницу и попробуйте снова.", 400)

    if security.rate_limit_exceeded():
        current_app.logger.warning("Rate limit сработал для %s", security.client_ip())
        return _contact_error("Слишком много заявок. Попробуйте позже.", 429)

    clean, errors = security.validate_contact(request.form)
    honeypot = security.sanitize_text(request.form.get("website"), 100)
    if honeypot:
        # Ловушка заполнена ботом: отвечаем «успехом», но ничего не сохраняем.
        current_app.logger.info("Honeypot сработал для %s", security.client_ip())
        return _contact_ok()

    if errors:
        return _contact_error(errors[0], 400, errors)

    record = storage.add_message(
        {
            "name": clean["name"],
            "contact": clean["contact"],
            "message": clean["message"],
            "ip": security.client_ip(),
            "user_agent": request.user_agent.string,
        }
    )
    _notify_telegram(record)
    current_app.logger.info("Новая заявка №%s от %s", record["id"], clean["contact"])
    return _contact_ok()


def _contact_ok():
    payload = {"ok": True, "message": "Заявка отправлена. Отвечу в течение рабочего дня."}
    if _wants_json():
        return jsonify(payload), 200
    return redirect(url_for("main.index") + "?contact=sent#contacts", code=303)


def _contact_error(message: str, status: int, errors: list[str] | None = None):
    payload = {"ok": False, "message": message, "errors": errors or [message]}
    if _wants_json():
        return jsonify(payload), status
    return redirect(
        url_for("main.index") + f"?contact=error&msg={urllib.parse.quote(message)}#contacts",
        code=303,
    )


def _wants_json() -> bool:
    if request.is_json:
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept or request.headers.get("X-Requested-With") == "XMLHttpRequest"
