#!/usr/bin/env python
"""Ежедневное резервное копирование файлов и данных сайта.

    python scripts/backup.py            # создать бэкап
    python scripts/backup.py --prune 30 # создать бэкап и удалить старше 30 дней

Рекомендуется запускать по cron:

    17 3 * * * cd /srv/matalin-portfolio && /usr/bin/python3 scripts/backup.py --prune 30
"""
from __future__ import annotations

import argparse
import fnmatch
import sys
import tarfile
import time
from pathlib import Path, PurePosixPath

BASE = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = BASE / "backups"

SOURCE_DIRS = ["data", "logs"]
SOURCE_FILES = [".env"]
IGNORE_PATTERNS = ("*.tmp", "*.broken", "__pycache__", "*.pyc", ".DS_Store", "Thumbs.db")


def _ignore(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    """Пропускает временные файлы и служебные каталоги."""
    name = PurePosixPath(tarinfo.name).name
    if any(fnmatch.fnmatch(name, pattern) for pattern in IGNORE_PATTERNS):
        return None
    return tarinfo


def make_backup(target: Path) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d_%H-%M")
    archive = target / f"backup_{stamp}.tar.gz"

    with tarfile.open(archive, "w:gz") as tar:
        for name in SOURCE_DIRS:
            path = BASE / name
            if path.is_dir():
                tar.add(path, arcname=name, filter=_ignore)
        for name in SOURCE_FILES:
            path = BASE / name
            if path.is_file():
                tar.add(path, arcname=name)

    return archive


def prune(target: Path, days: int) -> list[Path]:
    cutoff = time.time() - days * 86400
    removed = []
    for archive in target.glob("backup_*.tar.gz"):
        if archive.stat().st_mtime < cutoff:
            archive.unlink()
            removed.append(archive)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Резервное копирование сайта")
    parser.add_argument("--target", default=str(DEFAULT_TARGET), help="каталог для бэкапов")
    parser.add_argument("--prune", type=int, default=0, metavar="DAYS", help="удалить бэкапы старше N дней")
    args = parser.parse_args()

    target = Path(args.target)
    archive = make_backup(target)
    size_kb = round(archive.stat().st_size / 1024, 1)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Создан бэкап: {archive} ({size_kb} КБ)")

    if args.prune:
        for removed in prune(target, args.prune):
            print(f"  удалён устаревший бэкап: {removed.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
