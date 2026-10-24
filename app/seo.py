"""Микроразметка Schema.org (JSON-LD) для SEO."""
from __future__ import annotations

import json
from typing import Any

from flask import current_app

from . import content


def _base() -> str:
    return current_app.config["BASE_URL"]


def person_schema() -> str:
    cfg = current_app.config
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": cfg["SITE_NAME"],
        "jobTitle": "Frontend-разработчик, создатель Telegram-ассистентов",
        "url": f"{_base()}/",
        "email": f"mailto:{cfg['EMAIL']}",
        "sameAs": [cfg["GITHUB_URL"], f"https://t.me/{cfg['TELEGRAM_USERNAME']}"],
        "knowsAbout": ["React", "TypeScript", "Python", "Telegram Bot API", "Frontend", "UX"],
        "worksFor": {
            "@type": "Organization",
            "name": cfg["SITE_NAME"],
            "url": f"{_base()}/",
        },
    }
    return json.dumps(data, ensure_ascii=False)


def website_schema() -> str:
    cfg = current_app.config
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": f"{cfg['SITE_NAME']} — Portfolio",
        "url": f"{_base()}/",
        "inLanguage": "ru-RU",
        "publisher": {"@type": "Person", "name": cfg["SITE_NAME"]},
    }
    return json.dumps(data, ensure_ascii=False)


def case_schema(case: content.Case) -> str:
    cfg = current_app.config
    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": case.title,
        "description": case.summary,
        "url": f"{_base()}/projects/{case.slug}/",
        "author": {"@type": "Person", "name": cfg["SITE_NAME"]},
        "dateCreated": case.year,
        "keywords": ", ".join(case.stack),
        "image": f"{_base()}{case.cover}",
        "codeRepository": case.github,
    }
    return json.dumps(data, ensure_ascii=False)
