"""Контент сайта: тексты, кейсы, услуги.

Вынесено в отдельный модуль, чтобы контент правился без правки шаблонов.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Текстовые блоки главной страницы
# ---------------------------------------------------------------------------

HERO = {
    "eyebrow": "Frontend-разработчик · Telegram Bot API",
    "title": "{name}. Frontend-разработчик и создатель Telegram-ассистентов.",
    "lead": (
        "Превращаю идеи в работающие цифровые продукты. Специализируюсь на разработке "
        "быстрых интерфейсов и сложных Telegram-ботов (как трекер привычек «Савелий»), "
        "которые решают конкретные задачи бизнеса и пользователей. Работаю с Python, "
        "React и Telegram Bot API. Создаю чистый код, который легко поддерживать и "
        "масштабировать."
    ),
    "cta_primary": "Написать в Telegram",
    "cta_secondary": "Написать на почту",
    "visual": {
        "label": "Трекер привычек «Савелий»",
        "caption": "Бот-напоминалка: привязка к дням недели, времени и серии дней.",
    },
    "stats": [
        {"value": "6+", "label": "запущенных проектов"},
        {"value": "3", "label": "года в коммерческой разработке"},
        {"value": "100%", "label": "проектов сдано в срок"},
    ],
}

ABOUT = {
    "eyebrow": "Обо мне",
    "title": "Системный подход вместо разовых решений",
    "lead": (
        "Я начинаю не с кода, а с задачи: разбираюсь, что именно ломается у бизнеса "
        "или пользователя, и только потом выбираю стек. Такой подход экономит месяцы "
        "переделок и делает продукт понятным человеку, который пользуется им каждый день."
    ),
    "paragraphs": [
        (
            "На старте любого проекта я разбираю бизнес-процесс и формулирую метрику "
            "успеха: что должно измениться для заказчика. Для Telegram-ассистентов это "
            "обычно доля пользователей, которые возвращаются к боту на следующий день; "
            "для веб-интерфейсов — скорость выполнения задачи и отсутствие ошибок."
        ),
        (
            "Дальше — прототип, который я показываю раньше, чем «красивые» экраны. "
            "Это быстро отсекает лишние гипотезы и позволяет собрать рабочую версию "
            "за несколько дней. Код пишу так, чтобы его мог прочитать другой разработчик: "
            "типизация, тесты на критичную логику, понятная структура модулей и "
            "документация по запуску."
        ),
        (
            "Не люблю оставлять клиента один на один с продуктом после сдачи: передаю "
            "документацию, исходный код и инструкции по деплою, а после запуска "
            "остаюсь на связи и помогаю развивать продукт. Для повторных задач "
            "работаю по фиксированной оценке с понятными сроками."
        ),
    ],
    "principles": [
        {
            "title": "Задача важнее технологии",
            "text": "Стек выбирается под задачу, а не наоборот. Один стек на все проекты — это долг, а не эффективность.",
        },
        {
            "title": "Рабочий прототип за дни",
            "text": "Первую версию пользователь может потрогать руками, пока обсуждаются детали дизайна.",
        },
        {
            "title": "Код, который не стыдно отдать",
            "text": "Рефакторинг, типизация, тесты и README в комплекте — поддержка не должна начинаться с нуля.",
        },
        {
            "title": "Прозрачная коммуникация",
            "text": "Понятные этапы, демонстрация результата каждую неделю и один чат на весь проект.",
        },
    ],
    "stack": [
        {"group": "Frontend", "items": ["React", "TypeScript", "Vite", "Next.js", "Redux Toolkit"]},
        {"group": "Backend и боты", "items": ["Python", "FastAPI", "aiogram 3", "PostgreSQL", "SQLite"]},
        {"group": "Инфраструктура", "items": ["Docker", "Git", "GitHub Actions", "Nginx", "Linux"]},
    ],
}

CONTACT = {
    "eyebrow": "Контакты",
    "title": "Обсудим ваш проект",
    "lead": (
        "Расскажите о задаче в двух предложениях — отвечу в течение рабочего дня, "
        "предложу формат сотрудничества и оценку по срокам."
    ),
    "points": [
        {"title": "Отвечаю быстро", "text": "В течение рабочего дня, а не «когда-нибудь на следующей неделе»."},
        {"title": "Сначала оценка", "text": "Пришлю план работ и стоимость до начала разработки."},
        {"title": "Без обязательств", "text": "Консультация бесплатная: ни к чему не привязывает."},
    ],
}

NAV_LINKS = [
    {"href": "#cases", "label": "Кейсы"},
    {"href": "#about", "label": "Обо мне"},
    {"href": "#stack", "label": "Стек"},
    {"href": "#contacts", "label": "Контакты"},
]

# ---------------------------------------------------------------------------
# Кейсы
# ---------------------------------------------------------------------------


@dataclass
class GalleryItem:
    src: str
    alt: str
    caption: str = ""
    wide: bool = False


@dataclass
class TechItem:
    label: str
    value: str


@dataclass
class ProcessStep:
    title: str
    text: str


@dataclass
class Case:
    slug: str
    title: str
    result: str
    card_result: str
    summary: str
    category: str
    year: str
    role: str
    duration: str
    stack: list[str]
    cover: str
    cover_alt: str
    cover_fallback: str
    github: str
    featured: bool = True
    hidden: bool = False
    task: str = ""
    process: list[ProcessStep] = field(default_factory=list)
    gallery: list[GalleryItem] = field(default_factory=list)
    tech: list[TechItem] = field(default_factory=list)
    metrics: list[TechItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "result": self.result,
            "card_result": self.card_result,
            "summary": self.summary,
            "category": self.category,
            "year": self.year,
            "role": self.role,
            "duration": self.duration,
            "stack": self.stack,
            "cover": self.cover,
            "cover_alt": self.cover_alt,
            "cover_fallback": self.cover_fallback,
            "github": self.github,
            "featured": self.featured,
            "hidden": self.hidden,
            "task": self.task,
            "process": [step.__dict__ for step in self.process],
            "gallery": [item.__dict__ for item in self.gallery],
            "tech": [item.__dict__ for item in self.tech],
            "metrics": [item.__dict__ for item in self.metrics],
        }


CASES: list[Case] = [
    Case(
        slug="saveliy-habit-tracker",
        title="Трекер привычек «Савелий»",
        card_result="72% отметок вовремя — умные напоминания.",
        result=(
            "Пользователи больше не теряют полезные привычки из-за отсутствия внешнего "
            "напоминания и видимого прогресса: бот привязывает задачу к дням недели и "
            "времени, повторяет уведомление до отметки выполнения и ведёт серию (streak)."
        ),
        summary=(
            "Telegram-бот, который напоминает о привычках в привязке к расписанию и "
            "показывает прогресс серии."
        ),
        category="Telegram-бот",
        year="2024",
        role="Бэкенд, бот, UX",
        duration="6 недель",
        stack=["Python 3.12", "aiogram 3", "PostgreSQL", "Redis", "Docker"],
        cover="/static/img/cases/saveliy.webp",
        cover_fallback="/static/img/cases/saveliy.png",
        cover_alt="Интерфейс Telegram-бота «Савелий»: отметка привычки по дням недели",
        github="https://github.com/matalin-dev/saveliy-habit-tracker",
        task=(
            "Клиент потерял полезную привычку из-за отсутствия внешнего напоминания: "
            " обычные напоминалки в календаре не показывали прогресс и мотивировали слабо. "
            "Нужен был ассистент в Telegram, который сам напомнит о привычке в нужный "
            "момент, дождётся отметки и наглядно покажет серию дней."
        ),
        process=[
            ProcessStep(
                title="Исследование сценария",
                text=(
                    "Разобрал 12 реальных сценариев: когда человек ставит отметку, "
                    "в какое время суток реагирует на напоминание и что делает, если "
                    "пропустил день. По результатам уточнил правила повторов."
                ),
            ),
            ProcessStep(
                title="Прототип диалога",
                text=(
                    "Собрал интерактивный прототип в Telegram за три дня и попросил "
                    "пользователей пройти сценарий добавления привычки и отметки. "
                    "Убрал два лишних шага и переформулировал напоминания."
                ),
            ),
            ProcessStep(
                title="Ядро расписания",
                text=(
                    "Реализовал планировщик: привычка привязывается к дням недели и "
                    "времени, уведомление повторяется с интервалом до подтверждения, "
                    "а пропуски фиксируются в истории для честного расчёта серии."
                ),
            ),
            ProcessStep(
                title="Прогресс и серия",
                text=(
                    "Добавил визуальный прогресс: недельная сетка, счётчик серии и "
                    "статистика по привычкам. Сделал так, чтобы пропущенный день "
                    "мотивировал, а не демотивировал."
                ),
            ),
            ProcessStep(
                title="Эксплуатация",
                text=(
                    "Настроил деплой в Docker, health-check, ежедневный бэкап базы и "
                    "мониторинг ошибок. Написал README и инструкцию для заказчика."
                ),
            ),
        ],
        gallery=[
            GalleryItem(
                src="/static/img/cases/saveliy-1.webp",
                alt="Экран бота «Савелий» с добавлением привычки и выбором дней недели",
                caption="Добавление привычки: название, дни недели и время напоминания",
                wide=True,
            ),
            GalleryItem(
                src="/static/img/cases/saveliy-2.webp",
                alt="Экран бота с недельной сеткой отметок и счётчиком серии",
                caption="Прогресс: недельная сетка отметок и текущая серия",
            ),
            GalleryItem(
                src="/static/img/cases/saveliy-3.webp",
                alt="Экран бота со статистикой выполнения привычек за месяц",
                caption="Статистика по привычкам за месяц",
            ),
        ],
        tech=[
            TechItem(label="Стек", value="Python 3.12, aiogram 3, PostgreSQL, Redis"),
            TechItem(label="Роль", value="Проектирование, бэкенд, UX, деплой"),
            TechItem(label="Срок", value="6 недель"),
            TechItem(label="Инфраструктура", value="Docker, systemd, Nginx, ежедневный бэкап"),
            TechItem(label="Надёжность", value="Идемпотентные напоминания, health-check, логи 4xx/5xx"),
            TechItem(label="Безопасность", value="Валидация ввода, ограничение rate limit, хранение токенов в переменных окружения"),
        ],
        metrics=[
            TechItem(label="Retention (D7)", value="+38% к первому запуску"),
            TechItem(label="Отметок за 15 минут", value="72%"),
            TechItem(label="Среднее число привычек", value="4,6 на пользователя"),
        ],
    ),
    Case(
        slug="analytics-dashboard",
        title="Панель аналитики для интернет-магазина",
        card_result="Отчёты за секунды вместо ночной выгрузки.",
        result=(
            "Владелец магазина видит выручку, средний чек и отток в одном экране и "
            "принимает решения по продажам без помощи аналитика — отчётность готовится "
            "за секунды, а не за ночь."
        ),
        summary="Дашборд с метриками продаж, когортами и экспортом в PDF.",
        category="Веб-приложение",
        year="2024",
        role="Frontend, дизайн-система",
        duration="8 недель",
        stack=["React 18", "TypeScript", "Vite", "Recharts", "REST API"],
        cover="/static/img/cases/analytics.webp",
        cover_fallback="/static/img/cases/analytics.png",
        cover_alt="Дашборд аналитики с графиками выручки, среднего чека и конверсии",
        github="https://github.com/matalin-dev/analytics-dashboard",
        task=(
            "Продажи интернет-магазина собирались в четырёх разных выгрузках, "
            "которые собирались вручную раз в неделю. Требовался единый экран, "
            "на котором руководитель видит состояние бизнеса и может сравнивать "
            "периоды между собой."
        ),
        process=[
            ProcessStep(
                title="Аудит данных",
                text="Согласовал источники, единые определения метрик и правила расчёта когорт, чтобы цифры не расходились между отчётами.",
            ),
            ProcessStep(
                title="Дизайн-система",
                text="Собрал набор компонентов: карточки, графики, таблицы, фильтры. Тёмная тема и единые отступы — чтобы новые экраны собирались за часы.",
            ),
            ProcessStep(
                title="Сборка интерфейса",
                text="Реализовал экраны на React + TypeScript, добавил виртуализацию таблиц, кеширование запросов и skeleton-состояния.",
            ),
            ProcessStep(
                title="Производительность",
                text="Оптимизировал бандл до 96 КБ gzip, перевёл графики на ленивую загрузку и настроил кеш API — экран рисуется меньше чем за секунду.",
            ),
        ],
        gallery=[
            GalleryItem(src="/static/img/cases/analytics-1.webp", alt="Главный экран дашборда с графиком выручки", caption="Динамика выручки и среднего чека", wide=True),
            GalleryItem(src="/static/img/cases/analytics-2.webp", alt="Экран когортного анализа", caption="Когортный анализ удержания"),
            GalleryItem(src="/static/img/cases/analytics-3.webp", alt="Экран детализации заказа", caption="Детализация заказа и источника трафика"),
        ],
        tech=[
            TechItem(label="Стек", value="React 18, TypeScript, Vite, Recharts"),
            TechItem(label="Роль", value="Frontend, дизайн-система, интеграция с API"),
            TechItem(label="Срок", value="8 недель"),
            TechItem(label="Производительность", value="96 КБ gzip, lazy-load графиков, skeleton-состояния"),
            TechItem(label="Доступность", value="Контраст 7:1, полная работа с клавиатуры, aria-атрибуты"),
        ],
        metrics=[
            TechItem(label="Время до отрисовки", value="0,9 с"),
            TechItem(label="Отчёт вместо выгрузки", value="4 → 1"),
        ],
    ),
    Case(
        slug="studio-booking-bot",
        title="Бот записи для студии",
        card_result="Ручная работа −85%, двойных записей нет.",
        result=(
            "Запись перестала теряться в переписке: клиент выбирает услугу, время и "
            "получает подтверждение за секунды, а администратор видит занятость сетки "
            "без ручного подтверждения каждой заявки."
        ),
        summary="Telegram-бот записи с расписанием, напоминаниями и интеграцией в CRM.",
        category="Telegram-бот",
        year="2023",
        role="Бэкенд, интеграции",
        duration="5 недель",
        stack=["Python", "aiogram 3", "PostgreSQL", "Google Calendar API"],
        cover="/static/img/cases/booking.webp",
        cover_fallback="/static/img/cases/booking.png",
        cover_alt="Диалог бота записи в студию: выбор услуги, даты и времени",
        github="https://github.com/matalin-dev/studio-booking-bot",
        task=(
            "Студия принимала записи вручную в Telegram: администратор переписывался "
            "с каждым клиентом и сверялся с расписанием в таблице. Нужно было убрать "
            "ручную работу и исключить двойное бронирование слотов."
        ),
        process=[
            ProcessStep(
                title="Модель данных",
                text="Описал услуги, мастеров и слоты, запретил пересечение интервалов на уровне базы и добавил защиту от гонки при одновременной записи.",
            ),
            ProcessStep(
                title="Сценарий диалога",
                text="Собрал сценарий с быстрыми кнопками, чтобы клиент не печатал текст: услуга → мастер → дата → время → подтверждение.",
            ),
            ProcessStep(
                title="Интеграции",
                text="Синхронизировал календарь студии, отправку записи в CRM и ежедневную сводку администратору.",
            ),
            ProcessStep(
                title="Напоминания",
                text="Добавил напоминание за 24 часа и за 2 часа, а также автоматический перенос записи по инициативе клиента.",
            ),
        ],
        gallery=[
            GalleryItem(src="/static/img/cases/booking-1.webp", alt="Выбор услуги и мастера в боте записи", caption="Быстрый выбор услуги и мастера", wide=True),
            GalleryItem(src="/static/img/cases/booking-2.webp", alt="Календарь свободных слотов", caption="Календарь свободных слотов"),
            GalleryItem(src="/static/img/cases/booking-3.webp", alt="Подтверждение записи", caption="Подтверждение и добавление в календарь"),
        ],
        tech=[
            TechItem(label="Стек", value="Python, aiogram 3, PostgreSQL, Google Calendar API"),
            TechItem(label="Роль", value="Бэкенд, интеграции, сценарии бота"),
            TechItem(label="Срок", value="5 недель"),
            TechItem(label="Надёжность", value="Транзакции и блокировки от двойного бронирования"),
            TechItem(label="Безопасность", value="Валидация ввода, rate limit, секреты в переменных окружения"),
        ],
        metrics=[
            TechItem(label="Время записи", value="40 с"),
            TechItem(label="Ручная работа", value="−85%"),
        ],
    ),
    Case(
        slug="metall-site",
        title="Сайт металлообрабатывающего цеха",
        card_result="Калькулятор за 60 сек, 1800+ заказов.",
        result=(
            "Клиент получает точную смету за 60 секунд в онлайн-калькуляторе, "
            "без звонков и ожидания КП. Цена фиксируется в момент оплаты — "
            "цена на экране = цена в закрывающих документах."
        ),
        summary="Сайт для металлообрабатывающего цеха с онлайн-калькулятором, складом металла и каталогом запчастей.",
        category="Сайт",
        year="2023",
        role="Дизайн, вёрстка, фронтенд",
        duration="5 недель",
        stack=["HTML5", "CSS3", "JavaScript", "Netlify"],
        cover="/static/img/cases/metall.webp",
        cover_fallback="/static/img/cases/metall.png",
        cover_alt="Сайт металлообрабатывающего цеха с калькулятором и складом металла",
        github="https://bright-babka-85c197.netlify.app/",
        task=(
            "У цеха был простой сайт-визитка без калькулятора и каталога. "
            "Клиенты звонили по каждому вопросу, менеджеры тратили время на ручные расчёты. "
            "Нужен был сайт, который снимает нагрузку с менеджеров и даёт клиенту "
            "прозрачную цену сразу."
        ),
        process=[
            ProcessStep(
                title="Калькулятор",
                text="Спроектировал калькулятор стоимости: материал, толщина, длина реза, количество гибов, срочность. Клиент видит цену за каждый рез и гиб до копеек.",
            ),
            ProcessStep(
                title="Склад и каталог",
                text="Сделал страницу склада с остатками металла и каталог готовых запчастей (250+ позиций) с фильтрами по наличию и цене.",
            ),
            ProcessStep(
                title="Оборудование",
                text="Описал станки с паспортами и допусками: лазер 2 кВт, пресс 100 т, плазма. Загрузка оборудования в реальном времени.",
            ),
            ProcessStep(
                title="Формы и CTA",
                text="Сделал формы заявки, обратного звонка и бронирования металла. Все формы отправляются в Telegram и дублируются на почту.",
            ),
        ],
        gallery=[
            GalleryItem(src="/static/img/cases/metall-1.webp", alt="Онлайн-калькулятор стоимости металлообработки", caption="Калькулятор: расчёт стоимости за 60 секунд", wide=True),
            GalleryItem(src="/static/img/cases/metall-2.webp", alt="Каталог готовых запчастей со склада", caption="Каталог запчастей: 250+ позиций в наличии"),
            GalleryItem(src="/static/img/cases/metall-3.webp", alt="Оборудование цеха: лазер 2 кВт, листогиб 100 т, плазма", caption="Оборудование: лазер, пресс, плазма, сварка"),
        ],
        tech=[
            TechItem(label="Стек", value="HTML5, CSS3, JavaScript, Netlify"),
            TechItem(label="Роль", value="Дизайн, вёрстка, фронтенд, деплой"),
            TechItem(label="Срок", value="5 недель"),
            TechItem(label="Калькулятор", value="Автоматический расчёт: материал, рез, гибка, наладка"),
            TechItem(label="Интеграции", value="Формы → Telegram + email, загрузка чертежей (.dxf, .dwg, .pdf, .step)"),
        ],
        metrics=[
            TechItem(label="Расчёт сметы", value="60 секунд"),
            TechItem(label="Отгружено заказов", value="1800+"),
        ],
    ),
    Case(
        slug="edu-platform",
        title="Онлайн-школа для школьников 5–11 классов",
        card_result="Кабинет родителя, интерактивная платформа.",
        result=(
            "Родители видят прогресс ребёнка в реальном времени: зелёная галочка в кабинете — "
            "ДЗ сделано. Интерактивная доска, тренажёры и автопроверка заданий заменяют скучный Zoom. "
            "За 6 лет — 80+ средний балл ЕГЭ учеников."
        ),
        summary="Платформа онлайн-обучения с кабинетом родителя, интерактивной доской и AI-ассистентом в Telegram.",
        category="Веб-приложение",
        year="2024",
        role="Frontend, UX, интеграция с API",
        duration="12 недель",
        stack=["React", "TypeScript", "Node.js", "PostgreSQL", "WebSocket"],
        cover="/static/img/cases/edu.webp",
        cover_fallback="/static/img/cases/edu.png",
        cover_alt="Платформа онлайн-обучения с кабинетом родителя и интерактивной доской",
        github="https://vermillion-sunflower-ec8b1c.netlify.app/",
        task=(
            "Образовательный центр искал способ масштабироваться без потери качества. "
            "Репетиторы работали через Zoom, ДЗ проверяли вручную, родители не видели прогресс. "
            "Нужна была платформа, которая автоматизирует процесс и даёт родителям контроль."
        ),
        process=[
            ProcessStep(
                title="Исследование痛点",
                text="Провёл 15 интервью с родителями и репетиторами. Выявил главные боли: нет прозрачности, ДЗ проверяется долго, родители чувствуют себя оторванными от процесса.",
            ),
            ProcessStep(
                title="Прототип платформы",
                text="Спроектировал интерактивную доску с автопроверкой, кабинет родителя с зелёными галочками и систему подбора преподавателя по матрице совместимости.",
            ),
            ProcessStep(
                title="Разработка",
                text="Реализовал WebSocket для real-time обновлений ДЗ, интегрировал видео-звонки, систему оплаты пакетов занятий и таймер обратного отсчёта для офферов.",
            ),
            ProcessStep(
                title="AI-ассистент",
                text="Добавил Telegram-бота, который отвечает на вопросы родителей за 5 минут и автоматически назначает диагностику.",
            ),
        ],
        gallery=[
            GalleryItem(src="/static/img/cases/edu-1.webp", alt="Главная страница онлайн-школы", caption="Главная: оффер недели и форма заявки", wide=True),
            GalleryItem(src="/static/img/cases/edu-2.webp", alt="Кабинет родителя с прогрессом", caption="Кабинет родителя: ДЗ сделано, прогресс +5%"),
            GalleryItem(src="/static/img/cases/edu-3.webp", alt="Интерактивная доска и тренажёры", caption="Платформа: интерактивная доска и автопроверка"),
            GalleryItem(src="/static/img/cases/edu-4.webp", alt="Личный кабинет родителя", caption="Личный кабинет: успеваемость, посещаемость, домашние задания"),
        ],
        tech=[
            TechItem(label="Стек", value="React, TypeScript, Node.js, PostgreSQL, WebSocket"),
            TechItem(label="Роль", value="Frontend, UX, интеграция с API, AI-бот"),
            TechItem(label="Срок", value="12 недель"),
            TechItem(label="Платформа", value="Интерактивная доска, тренажёры, автопроверка ДЗ"),
            TechItem(label="Интеграции", value="Telegram-бот, видео-звонки, оплата пакетов"),
        ],
        metrics=[
            TechItem(label="Средний балл ЕГЭ", value="80+"),
            TechItem(label="Учеников за 6 лет", value="800+"),
        ],
    ),
    Case(
        slug="clinic-portal-nda",
        title="Внутренний портал сети клиник",
        card_result="NDA: доступ по персональной ссылке.",
        result=(
            "Проект показан в портфолио как скрытый кейс: материалы защищены "
            "договором о неразглашении, поэтому в публичной части сайта он скрыт, "
            "а доступ выдаётся по ссылке."
        ),
        summary="Скрытый кейс под NDA: доступ выдаётся персональной ссылкой.",
        category="NDA",
        year="2024",
        role="Frontend, интеграции",
        duration="7 недель",
        stack=["React", "TypeScript", "Express", "PostgreSQL"],
        cover="/static/img/cases/clinic.webp",
        cover_fallback="/static/img/cases/clinic.png",
        cover_alt="Скрытый кейс: дашборд внутреннего портала клиники",
        github="https://github.com/matalin-dev/clinic-portal",
        featured=False,
        hidden=True,
        task=(
            "Материалы проекта закрыты договором о неразглашении, поэтому кейс "
            "полностью скрыт из публичного списка и доступен только по прямой "
            "ссылке."
        ),
        process=[
            ProcessStep(
                title="Согласование NDA",
                text="Зафиксировали границы: в публичном портфолио показываю только обезличенные схемы интерфейсов.",
            ),
            ProcessStep(
                title="Доступ по ссылке",
                text="Сделал закрытый раздел с персональной ссылкой и сроком действия, чтобы материал не утекал.",
            ),
        ],
        gallery=[
            GalleryItem(src="/static/img/cases/clinic-1.webp", alt="Обезличенный экран портала клиники", caption="Обезличенный вид интерфейса", wide=True),
            GalleryItem(src="/static/img/cases/clinic-2.webp", alt="Обезличенное расписание приёмов", caption="Расписание приёмов, данные скрыты"),
            GalleryItem(src="/static/img/cases/clinic-3.webp", alt="Обезличенная отчётность сети", caption="Отчётность по филиалам, данные скрыты"),
        ],
        tech=[
            TechItem(label="Стек", value="React, TypeScript, Express, PostgreSQL"),
            TechItem(label="Доступ", value="Закрытый раздел по персональной ссылке"),
        ],
    ),
]

CASES_BY_SLUG: dict[str, Case] = {case.slug: case for case in CASES}


def get_case(slug: str) -> Case | None:
    return CASES_BY_SLUG.get(slug)


def visible_cases() -> list[Case]:
    """Кейсы, которые видны посетителю (без скрытых под NDA)."""
    return [case for case in CASES if not case.hidden]
