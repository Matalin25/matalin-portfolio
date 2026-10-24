"""Хранилище состояния: флаги скрытия кейсов и заявки с формы.

Данные лежат в JSON-файлах рядом с проектом (каталог data/). Запись
атомарная: сначала во временный файл, затем os.replace — файл никогда не
остаётся в «полусломанном» состоянии. Для продакшена каталог data/ должен
быть включён в ежедневный бэкап (scripts/backup.py).
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import current_app

_lock = threading.Lock()


def _data_dir() -> Path:
    path = Path(current_app.config["DATA_DIR"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        backup = path.with_suffix(path.suffix + ".broken")
        try:
            os.replace(path, backup)
        except OSError:
            pass
        return default


def _write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Состояние кейсов
# ---------------------------------------------------------------------------


def load_case_state() -> dict[str, dict[str, Any]]:
    """Возвращает {slug: {"hidden": bool}} — состояние из админ-панели."""
    data = _read_json(_data_dir() / "cases.json", {})
    return data if isinstance(data, dict) else {}


def is_case_hidden(slug: str, default: bool = False) -> bool:
    state = load_case_state().get(slug)
    if isinstance(state, dict) and "hidden" in state:
        return bool(state["hidden"])
    return default


def set_case_hidden(slug: str, hidden: bool) -> bool:
    with _lock:
        path = _data_dir() / "cases.json"
        state = _read_json(path, {})
        if not isinstance(state, dict):
            state = {}
        state[slug] = {"hidden": bool(hidden), "updated_at": _now()}
        _write_json(path, state)
    return bool(hidden)


# ---------------------------------------------------------------------------
# Заявки с формы обратной связи
# ---------------------------------------------------------------------------


def add_message(payload: dict[str, str]) -> dict[str, Any]:
    """Сохраняет заявку в data/messages.json и возвращает её с id."""
    with _lock:
        path = _data_dir() / "messages.json"
        items = _read_json(path, [])
        if not isinstance(items, list):
            items = []
        record = {
            "id": int(datetime.now().timestamp() * 1000),
            "created_at": _now(),
            "name": payload.get("name", ""),
            "contact": payload.get("contact", ""),
            "message": payload.get("message", ""),
            "ip": payload.get("ip", ""),
            "user_agent": payload.get("user_agent", "")[:300],
            "status": "new",
        }
        items.append(record)
        _write_json(path, items)
    return record


def list_messages(limit: int = 100) -> list[dict[str, Any]]:
    items = _read_json(_data_dir() / "messages.json", [])
    if not isinstance(items, list):
        return []
    return list(reversed(items))[:limit]


def set_message_status(message_id: int, status: str) -> bool:
    with _lock:
        path = _data_dir() / "messages.json"
        items = _read_json(path, [])
        if not isinstance(items, list):
            return False
        found = False
        for item in items:
            if isinstance(item, dict) and item.get("id") == message_id:
                item["status"] = status
                found = True
        if found:
            _write_json(path, items)
    return found


def delete_message(message_id: int) -> bool:
    with _lock:
        path = _data_dir() / "messages.json"
        items = _read_json(path, [])
        if not isinstance(items, list):
            return False
        remaining = [i for i in items if not (isinstance(i, dict) and i.get("id") == message_id)]
        if len(remaining) == len(items):
            return False
        _write_json(path, remaining)
    return True


def count_new_messages() -> int:
    return sum(1 for m in list_messages(500) if m.get("status") == "new")
