#!/usr/bin/env python
"""Генерация обложек и галерей для кейсов.

Скрипт рисует «макеты интерфейсов» (чат-бот, дашборд, страницу сайта) и
сохраняет их в WebP + PNG (fallback) в app/static/img/cases.

    python scripts/make_images.py

Зависимости: Pillow. Готовые файлы уже лежат в репозитории — запускать скрипт
нужно только при изменении текстов или цветов.
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "app" / "static" / "img"
CASES = OUT / "cases"

BG = (10, 14, 20)
SURFACE = (18, 26, 38)
SURFACE_2 = (23, 33, 48)
BORDER = (38, 52, 72)
TEXT = (231, 237, 247)
MUTED = (142, 155, 178)

PALETTE = {
    "blue": ((91, 140, 255), (34, 211, 238)),
    "violet": ((167, 139, 250), (91, 140, 255)),
    "green": ((52, 211, 153), (34, 211, 238)),
    "orange": ((251, 146, 60), (248, 113, 113)),
    "pink": ((244, 114, 182), (167, 139, 250)),
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def gradient(size: tuple[int, int], c1: tuple[int, int, int], c2: tuple[int, int, int], angle: str = "diagonal") -> Image.Image:
    w, h = size
    base = Image.new("RGB", (w, h), c1)
    draw = ImageDraw.Draw(base)
    span = w + h
    for i in range(span):
        t = i / max(span - 1, 1)
        color = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        if angle == "diagonal":
            draw.line([(i, 0), (0, i)], fill=color)
        else:
            draw.line([(0, i), (w, i)], fill=color)
    return base


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ---------------------------------------------------------------------------
# Сцена: чат-бот
# ---------------------------------------------------------------------------

def scene_chat(size, accent, title, bubbles, footer=None, wide_bars=None):
    w, h = size
    img = gradient((w, h), mix(BG, accent[0], 0.08), BG)
    draw = ImageDraw.Draw(img)

    pad = int(w * 0.07)
    win = (pad, int(h * 0.09), w - pad, h - int(h * 0.09))
    rounded(draw, win, 24, fill=SURFACE, outline=BORDER, width=2)

    # Шапка
    head_h = int(h * 0.13)
    rounded(draw, (win[0], win[1], win[2], win[1] + head_h), 24, fill=SURFACE_2)
    draw.rectangle((win[0], win[1] + head_h - 24, win[2], win[1] + head_h), fill=SURFACE_2)
    draw.ellipse((win[0] + 18, win[1] + head_h / 2 - 15, win[0] + 48, win[1] + head_h / 2 + 15), fill=accent[0])
    draw.text((win[0] + 60, win[1] + head_h / 2 - 11), title, font=font(int(h * 0.045), True), fill=TEXT)
    for i in range(3):
        cx = win[2] - 24 - i * 16
        draw.ellipse((cx - 3, win[1] + head_h / 2 - 3, cx + 3, win[1] + head_h / 2 + 3), fill=MUTED)

    # Пузыри
    y = win[1] + head_h + 22
    for align, text, style in bubbles:
        f = font(int(h * 0.042), style == "bold")
        tw = draw.textlength(text, font=f)
        bw = min(tw + 36, win[2] - win[0] - 80)
        bh = int(h * 0.11)
        x = win[0] + 22 if align == "left" else win[2] - 22 - bw
        fill = SURFACE_2 if align == "left" else mix(accent[0], accent[1], 0.4)
        rounded(draw, (x, y, x + bw, y + bh), 16, fill=fill)
        draw.text((x + 18, y + bh / 2 - int(h * 0.028)), text, font=f, fill=TEXT if align == "left" else BG)
        y += bh + 12

    # Нижний блок (прогресс / неделя)
    if wide_bars:
        f = font(int(h * 0.038), True)
        draw.text((win[0] + 22, y + 4), wide_bars[0], font=f, fill=MUTED)
        y += int(h * 0.07)
        cell = min(int((win[2] - win[0] - 44) / len(wide_bars[1])), int(h * 0.1))
        for i, (label, done) in enumerate(wide_bars[1]):
            x = win[0] + 22 + i * (cell + 8)
            fill = mix(accent[0], accent[1], 0.35) if done else SURFACE_2
            rounded(draw, (x, y, x + cell, y + cell), 12, fill=fill, outline=BORDER)
            draw.text((x + cell / 2 - 11, y + cell / 2 - 11), label, font=font(int(h * 0.03)), fill=TEXT if done else MUTED)
        y += cell + 12

    if footer:
        rounded(draw, (win[0] + 22, y, win[2] - 22, y + int(h * 0.1)), 14, fill=SURFACE_2)
        draw.text((win[0] + 38, y + int(h * 0.028)), footer, font=font(int(h * 0.04)), fill=TEXT)

    return img


# ---------------------------------------------------------------------------
# Сцена: дашборд
# ---------------------------------------------------------------------------

def scene_dashboard(size, accent, title, kind="bars", kpis=3, sidebar=True):
    w, h = size
    img = gradient((w, h), mix(BG, accent[0], 0.07), BG)
    draw = ImageDraw.Draw(img)

    pad = int(w * 0.05)
    win = (pad, int(h * 0.08), w - pad, h - int(h * 0.08))
    rounded(draw, win, 22, fill=SURFACE, outline=BORDER, width=2)

    head_h = int(h * 0.11)
    rounded(draw, (win[0], win[1], win[2], win[1] + head_h), 22, fill=SURFACE_2)
    draw.rectangle((win[0], win[1] + head_h - 22, win[2], win[1] + head_h), fill=SURFACE_2)
    draw.text((win[0] + 20, win[1] + head_h / 2 - 12), title, font=font(int(h * 0.048), True), fill=TEXT)

    body_top = win[1] + head_h + 16
    left = win[0] + 16
    right = win[2] - 16

    if sidebar:
        sb_w = int(w * 0.16)
        rounded(draw, (left, body_top, left + sb_w, win[3] - 16), 14, fill=SURFACE_2)
        for i in range(7):
            y = body_top + 18 + i * int(h * 0.075)
            if y + 12 > win[3] - 30:
                break
            color = accent[0] if i == 1 else BORDER
            rounded(draw, (left + 16, y, left + 16 + sb_w - 32, y + 12), 6, fill=color)
        left = left + sb_w + 16

    # KPI-плитки
    kpi_h = int(h * 0.16)
    gap = 14
    kpi_w = (right - left - gap * (kpis - 1)) / kpis
    for i in range(kpis):
        x = left + i * (kpi_w + gap)
        rounded(draw, (x, body_top, x + kpi_w, body_top + kpi_h), 14, fill=SURFACE_2, outline=BORDER)
        rounded(draw, (x + 16, body_top + 18, x + 16 + kpi_w * 0.42, body_top + 26), 4, fill=BORDER)
        value = ["₽ 4,2 млн", "37,4%", "128 заказов"][i % 3]
        draw.text((x + 16, body_top + 36), value, font=font(int(h * 0.055), True), fill=TEXT)
        draw.text((x + 16, body_top + kpi_h - 30), ["Выручка", "Конверсия", "Заказы"][i % 3], font=font(int(h * 0.035)), fill=MUTED)

    chart_top = body_top + kpi_h + 16
    rounded(draw, (left, chart_top, right, win[3] - 16), 16, fill=SURFACE_2, outline=BORDER)

    if kind == "bars":
        n = 12
        base = win[3] - 40
        bw = (right - left - 48) / n
        for i in range(n):
            t = (i % 5 + 1) / 5 + (i * 0.07) % 0.6
            bh = (base - chart_top - 30) * min(t, 1.0)
            x = left + 24 + i * bw
            color = mix(accent[0], accent[1], i / max(n - 1, 1))
            rounded(draw, (x, base - bh, x + bw * 0.55, base), 6, fill=color)
    else:
        pts = []
        n = 14
        base = win[3] - 40
        for i in range(n):
            t = (i % 4 + 1) / 4
            x = left + 24 + i * (right - left - 48) / (n - 1)
            y = base - (base - chart_top - 30) * min(t, 1.0)
            pts.append((x, y))
        draw.line(pts, fill=accent[0], width=4, joint="curve")
        for x, y in pts:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=accent[1])

    return img


# ---------------------------------------------------------------------------
# Сцена: страница сайта
# ---------------------------------------------------------------------------

def scene_page(size, accent, title, hero_title, with_form=True):
    w, h = size
    img = gradient((w, h), mix(BG, accent[0], 0.06), BG)
    draw = ImageDraw.Draw(img)

    pad = int(w * 0.05)
    win = (pad, int(h * 0.07), w - pad, h - int(h * 0.07))
    rounded(draw, win, 20, fill=SURFACE, outline=BORDER, width=2)

    head_h = int(h * 0.1)
    rounded(draw, (win[0], win[1], win[2], win[1] + head_h), 20, fill=SURFACE_2)
    draw.rectangle((win[0], win[1] + head_h - 20, win[2], win[1] + head_h), fill=SURFACE_2)
    for i in range(3):
        cx = win[0] + 20 + i * 16
        draw.ellipse((cx - 5, win[1] + head_h / 2 - 5, cx + 5, win[1] + head_h / 2 + 5), fill=BORDER)
    draw.text((win[0] + 80, win[1] + head_h / 2 - 10), title, font=font(int(h * 0.04)), fill=MUTED)

    top = win[1] + head_h + 18
    col_w = (win[2] - win[0] - 48) * (0.52 if with_form else 1)
    left = win[0] + 24

    rounded(draw, (left, top, left + col_w * 0.55, top + int(h * 0.09)), 8, fill=mix(accent[0], accent[1], 0.3))
    draw.text((left + 18, top + int(h * 0.028)), hero_title, font=font(int(h * 0.055), True), fill=BG)

    y = top + int(h * 0.14)
    for i in range(4):
        width = col_w * (0.9 - i * 0.12)
        rounded(draw, (left, y, left + width, y + 10), 5, fill=BORDER)
        y += 22

    y += 12
    for i in range(3):
        rounded(draw, (left + i * (int(col_w * 0.28) + 12), y, left + i * (int(col_w * 0.28) + 12) + int(col_w * 0.28), y + int(h * 0.16)), 12, fill=SURFACE_2, outline=BORDER)

    if with_form:
        fx = win[0] + 24 + col_w + 24
        fw = win[2] - 24 - fx
        rounded(draw, (fx, top, win[2] - 24, win[3] - 24), 14, fill=SURFACE_2, outline=BORDER)
        draw.text((fx + 18, top + 16), "Оставить заявку", font=font(int(h * 0.042), True), fill=TEXT)
        fy = top + int(h * 0.1)
        for _ in range(2):
            rounded(draw, (fx + 18, fy, win[2] - 42, fy + int(h * 0.1)), 10, fill=SURFACE)
            fy += int(h * 0.12)
        rounded(draw, (fx + 18, fy, win[2] - 42, fy + int(h * 0.14)), 10, fill=SURFACE)
        fy += int(h * 0.16)
        rounded(draw, (fx + 18, fy, win[2] - 120, fy + int(h * 0.09)), 12, fill=mix(accent[0], accent[1], 0.4))

    return img


# ---------------------------------------------------------------------------
# Каталог изображений
# ---------------------------------------------------------------------------


def build_covers():
    files = []

    # 1. Савелий — чат-бот
    files.append((
        "saveliy",
        lambda: scene_chat(
            (800, 500), PALETTE["green"], "Савелий",
            [("left", "Пора встать. Чтение — 20 минут.", "normal"),
             ("right", "Отметил", "bold"),
             ("left", "Отлично! Серия: 12 дней", "normal")],
            footer="Серия растёт каждый день",
            wide_bars=("Неделя", [("Пн", True), ("Вт", True), ("Ср", True), ("Чт", True), ("Пт", True), ("Сб", False), ("Вс", True)]),
        ),
    ))
    files.append((
        "saveliy-1",
        lambda: scene_chat(
            (1200, 750), PALETTE["green"], "Савелий — новая привычка",
            [("left", "Что хотите отслеживать?", "normal"),
             ("right", "Чтение", "bold")],
            footer="Дни недели: Пн, Ср, Пт · 09:30",
            wide_bars=("Выберите дни", [("Пн", True), ("Вт", False), ("Ср", True), ("Чт", False), ("Пт", True), ("Сб", False), ("Вс", False)]),
        ),
    ))
    files.append((
        "saveliy-2",
        lambda: scene_chat(
            (1200, 750), PALETTE["blue"], "Савелий — прогресс",
            [("left", "Отметьте выполнение", "normal")],
            footer="Серия: 12 дней · рекорд: 21",
            wide_bars=("Неделя", [("Пн", True), ("Вт", True), ("Ср", True), ("Чт", True), ("Пт", True), ("Сб", False), ("Вс", True)]),
        ),
    ))
    files.append((
        "saveliy-3",
        lambda: scene_chat(
            (1200, 750), PALETTE["violet"], "Савелий — статистика",
            [("left", "За месяц: 86% выполнения", "normal")],
            footer="Лучше всего: спорт · Хуже всего: английский",
            wide_bars=("Неделя", [("Пн", True), ("Вт", False), ("Ср", True), ("Чт", True), ("Пт", False), ("Сб", True), ("Вс", True)]),
        ),
    ))

    # 2. Парсинг бирж фриланса
    files.append((
        "otvet",
        lambda: scene_page((800, 500), PALETTE["orange"], "parsing-birja.netlify.app", "Упаковка услуг: 5 digital-направлений"),
    ))
    files.append((
        "otvet-1",
        lambda: scene_page((1200, 750), PALETTE["orange"], "parsing-birja.netlify.app", "Главная: заказы и отклики"),
    ))
    files.append((
        "otvet-2",
        lambda: scene_page((1200, 750), PALETTE["blue"], "parsing-birja.netlify.app", "Карточка заказа", with_form=False),
    ))
    files.append((
        "otvet-3",
        lambda: scene_page((1200, 750), PALETTE["green"], "parsing-birja.netlify.app", "Трекер откликов", with_form=False),
    ))
    files.append((
        "otvet-4",
        lambda: scene_page((1200, 750), PALETTE["violet"], "parsing-birja.netlify.app", "Отклик на Kwork", with_form=True),
    ))

    # 3. Запись в студию
    files.append((
        "booking",
        lambda: scene_chat(
            (800, 500), PALETTE["orange"], "Студия · запись",
            [("left", "Выберите услугу", "normal"),
             ("right", "Массаж 60 мин", "bold")],
            footer="Свободно сегодня: 12:30, 15:00, 18:30",
        ),
    ))
    files.append((
        "booking-1",
        lambda: scene_chat(
            (1200, 750), PALETTE["orange"], "Запись · услуга и мастер",
            [("left", "Кто вам нужен?", "normal"),
             ("right", "Анна, массаж", "bold"),
             ("left", "Выберите дату", "normal")],
        ),
    ))
    files.append((
        "booking-2",
        lambda: scene_chat(
            (1200, 750), PALETTE["blue"], "Запись · свободные слоты",
            [("right", "18:30", "bold")],
            footer="Подтверждено · напомним за 2 часа",
        ),
    ))
    files.append((
        "booking-3",
        lambda: scene_chat(
            (1200, 750), PALETTE["green"], "Запись · подтверждение",
            [("left", "Готово! Записали на среду", "normal"),
             ("right", "Спасибо", "bold")],
            footer="Добавлено в календарь студии",
        ),
    ))

    # 4. Сайт металлообрабатывающего цеха
    files.append((
        "metall",
        lambda: scene_page((800, 500), PALETTE["blue"], "matalin-portfolio.ru", "Металлообработка"),
    ))
    files.append((
        "metall-1",
        lambda: scene_page((1200, 750), PALETTE["blue"], "matalin-portfolio.ru", "Главная: калькулятор, склад, оборудование"),
    ))
    files.append((
        "metall-2",
        lambda: scene_page((1200, 750), PALETTE["green"], "matalin-portfolio.ru/calculator", "Калькулятор: расчёт за 60 секунд", with_form=True),
    ))
    files.append((
        "metall-3",
        lambda: scene_page((1200, 750), PALETTE["orange"], "matalin-portfolio.ru/parts", "Каталог запчастей: 250+ позиций в наличии", with_form=False),
    ))

    # 5. Онлайн-школа
    files.append((
        "edu",
        lambda: scene_dashboard((800, 500), PALETTE["green"], "Образовательная платформа", kind="bars"),
    ))
    files.append((
        "edu-1",
        lambda: scene_dashboard((1200, 750), PALETTE["green"], "Кабинет родителя · прогресс", kind="line"),
    ))
    files.append((
        "edu-2",
        lambda: scene_dashboard((1200, 750), PALETTE["blue"], "Интерактивная доска", kind="bars", kpis=3),
    ))
    files.append((
        "edu-3",
        lambda: scene_dashboard((1200, 750), PALETTE["violet"], "Автопроверка ДЗ · 5000 заданий ФИПИ", kind="line", kpis=2, sidebar=False),
    ))

    # 6. Скрытый кейс под NDA
    files.append((
        "clinic",
        lambda: scene_dashboard((800, 500), PALETTE["blue"], "Портал клиники · NDA", kind="line"),
    ))
    files.append((
        "clinic-1",
        lambda: scene_dashboard((1200, 750), PALETTE["blue"], "Портал клиники · обезличено", kind="line"),
    ))
    files.append((
        "clinic-2",
        lambda: scene_dashboard((1200, 750), PALETTE["violet"], "Расписание · обезличено", kind="bars", sidebar=False),
    ))
    files.append((
        "clinic-3",
        lambda: scene_dashboard((1200, 750), PALETTE["green"], "Отчётность · обезличено", kind="line", kpis=4),
    ))

    return files


def build_og_cover():
    w, h = 1200, 630
    img = gradient((w, h), (10, 14, 20), mix(BG, PALETTE["blue"][0], 0.22), angle="vertical")
    draw = ImageDraw.Draw(img)

    for i in range(9):
        r = 120 + i * 60
        draw.ellipse((w - 420 - r, -260 - r, w - 420 + r, -260 + r), outline=mix(BG, PALETTE["blue"][0], 0.10 + i * 0.03), width=2)

    draw.text((90, 170), "MATALIN", font=font(96, True), fill=TEXT)
    draw.text((90, 290), "Frontend-разработчик", font=font(44, True), fill=mix(TEXT, PALETTE["blue"][0], 0.35))
    draw.text((90, 350), "и создатель Telegram-ассистентов", font=font(44, True), fill=mix(TEXT, PALETTE["blue"][0], 0.35))
    rounded(draw, (90, 450, 90 + 330, 450 + 62), 31, fill=mix(PALETTE["blue"][0], PALETTE["blue"][1], 0.4))
    draw.text((126, 468), "matalin-portfolio.ru", font=font(24, True), fill=BG)
    return img


def build_favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="M">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#5b8cff"/>
      <stop offset="1" stop-color="#22d3ee"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="16" fill="#0a0e14"/>
  <rect x="6" y="6" width="52" height="52" rx="13" fill="url(#g)"/>
  <path d="M17 44V20h6l9 13 9-13h6v24h-6V31l-9 12-9-12v13z" fill="#05080d"/>
</svg>
"""
    (OUT / "favicon.svg").write_text(svg, encoding="utf-8")


def save(img: Image.Image, name: str, base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    webp = base / f"{name}.webp"
    png = base / f"{name}.png"
    img.save(webp, "WEBP", quality=82, method=6)
    img.save(png, "PNG", optimize=True)
    try:
        img.save(base / f"{name}.avif", "AVIF", quality=60)
    except (OSError, ValueError):
        pass


def main() -> None:
    build_favicon()

    for name, factory in build_covers():
        save(factory(), name, CASES)

    og = build_og_cover()
    save(og, "og-cover", OUT)

    print(f"Готово: изображения в {CASES} и {OUT}")


if __name__ == "__main__":
    main()
