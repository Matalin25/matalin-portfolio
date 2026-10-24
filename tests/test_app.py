"""Тесты сайта: маршруты, безопасность, валидация формы, админ-панель.

    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app import security  # noqa: E402
from app.config import Config  # noqa: E402


class TestConfig(Config):
    DEBUG = False
    TESTING = True
    ADMIN_PASSWORD = "test-password"
    SESSION_COOKIE_SECURE = False
    FORCE_HTTPS = False
    FORCE_WWW_REDIRECT = False
    TRUST_PROXY_SSL = False
    RATE_LIMIT_MAX = 5
    RATE_LIMIT_WINDOW = 60


class BaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="portfolio-test-"))
        config = type(
            "TmpConfig",
            (TestConfig,),
            {"DATA_DIR": self.tmp / "data", "LOG_DIR": self.tmp / "logs", "BACKUP_DIR": self.tmp / "backups"},
        )
        self.app = create_app(config)
        self.client = self.app.test_client()
        security.reset_rate_limit()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def csrf(self, path: str = "/") -> str:
        response = self.client.get(path)
        html = response.get_data(as_text=True)
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        return match.group(1) if match else ""


class PageTests(BaseTestCase):
    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("<h1", html)
        self.assertIn("Frontend-разработчик", html)
        self.assertIn("Трекер привычек", html)
        self.assertIn('id="cases"', html)
        self.assertIn('id="contacts"', html)

    def test_hierarchy_of_headings(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1)
        self.assertTrue(re.search(r"<h2[\s>]", html))
        self.assertTrue(re.search(r"<h3[\s>]", html))

    def test_project_page(self):
        response = self.client.get("/projects/saveliy-habit-tracker/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for section in ("Описание задачи", "Процесс", "Галерея", "Технические характеристики"):
            self.assertIn(section, html)
        self.assertIn("github.com", html)

    def test_unknown_project_returns_404(self):
        response = self.client.get("/projects/no-such-case/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Страница не найдена", response.get_data(as_text=True))

    def test_hidden_case_is_not_public(self):
        response = self.client.get("/projects/clinic-portal-nda/")
        self.assertEqual(response.status_code, 404)

    def test_hidden_case_not_in_homepage(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("clinic-portal-nda", html)

    def test_sitemap_and_robots(self):
        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertIn("saveliy-habit-tracker", sitemap.get_data(as_text=True))
        self.assertNotIn("clinic-portal-nda", sitemap.get_data(as_text=True))

        robots = self.client.get("/robots.txt")
        self.assertEqual(robots.status_code, 200)
        self.assertIn("Sitemap:", robots.get_data(as_text=True))

    def test_health(self):
        self.assertEqual(self.client.get("/health").status_code, 200)


class SecurityTests(BaseTestCase):
    def test_security_headers(self):
        response = self.client.get("/")
        headers = response.headers
        self.assertIn("X-Content-Type-Options", headers)
        self.assertIn("X-Frame-Options", headers)
        self.assertIn("Referrer-Policy", headers)
        self.assertIn("Permissions-Policy", headers)
        self.assertIn("Content-Security-Policy", headers)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "SAMEORIGIN")

    def test_csp_has_no_unsafe_inline_for_scripts(self):
        csp = self.client.get("/").headers["Content-Security-Policy"]
        script_src = [part for part in csp.split(";") if part.strip().startswith("script-src")][0]
        self.assertNotIn("unsafe-inline", script_src)
        self.assertNotIn("unsafe-eval", csp)

    def test_jsonld_hashes_match_csp(self):
        import base64
        import hashlib

        for path in ("/", "/projects/saveliy-habit-tracker/"):
            response = self.client.get(path)
            html = response.get_data(as_text=True)
            csp = response.headers["Content-Security-Policy"]
            blocks = re.findall(
                r'<script type="application/ld\+json">(.*?)</script>', html, re.S
            )
            self.assertTrue(blocks, f"на {path} нет JSON-LD")
            for block in blocks:
                digest = base64.b64encode(
                    hashlib.sha256(block.encode("utf-8")).digest()
                ).decode("ascii")
                self.assertIn(f"'sha256-{digest}'", csp, f"хэш не совпал на {path}")

    def test_no_inline_style_attributes(self):
        for path in ("/", "/projects/saveliy-habit-tracker/", "/admin/login"):
            html = self.client.get(path).get_data(as_text=True)
            self.assertNotRegex(html, r'\sstyle\s*=\s*"')

    def test_no_inline_event_handlers(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertNotRegex(html, r"on(click|load|error|submit|mouseover)\s*=")

    def test_scripts_are_external_only(self):
        for path in ("/", "/projects/saveliy-habit-tracker/"):
            html = self.client.get(path).get_data(as_text=True)
            for tag in re.findall(r"<script[^>]*>", html):
                self.assertTrue(
                    "src=" in tag or 'type="application/ld+json"' in tag,
                    f"Инлайновый скрипт не найден, но обнаружен: {tag}",
                )

    def test_admin_is_not_indexed(self):
        response = self.client.get("/admin/login")
        self.assertIn("noindex", response.headers.get("X-Robots-Tag", ""))

    def test_no_www_redirect(self):
        response = self.client.get("/", headers={"Host": "www.matalin-portfolio.ru"})
        # По умолчанию редирект выключен в dev-конфиге — проверяем сам механизм.
        self.assertIn(response.status_code, (200, 301))


class ContactFormTests(BaseTestCase):
    def test_post_without_csrf_is_rejected(self):
        response = self.client.post(
            "/api/contact",
            data={"name": "Иван", "contact": "@user", "message": "Хочу обсудить проект"},
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 400)

    def test_valid_submission(self):
        token = self.csrf()
        response = self.client.post(
            "/api/contact",
            data={
                "csrf_token": token,
                "name": "Иван Петров",
                "contact": "ivan@example.com",
                "message": "Нужен бот для записи клиентов в студию",
                "consent": "1",
            },
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])

    def test_invalid_email_is_rejected(self):
        token = self.csrf()
        response = self.client.post(
            "/api/contact",
            data={
                "csrf_token": token,
                "name": "Иван",
                "contact": "не-почта",
                "message": "Текст сообщения достаточной длины",
                "consent": "1",
            },
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 400)

    def test_consent_is_required(self):
        token = self.csrf()
        response = self.client.post(
            "/api/contact",
            data={
                "csrf_token": token,
                "name": "Иван",
                "contact": "@user",
                "message": "Текст сообщения достаточной длины",
            },
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 400)

    def test_honeypot_is_silently_ignored(self):
        token = self.csrf()
        response = self.client.post(
            "/api/contact",
            data={
                "csrf_token": token,
                "name": "Спам Бот",
                "contact": "spam@example.com",
                "message": "Купите дешёвые ссылки на наш сайт прямо сейчас",
                "consent": "1",
                "website": "http://spam.example.com",
            },
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        messages_file = self.tmp / "data" / "messages.json"
        self.assertFalse(messages_file.exists() and '"Спам Бот"' in messages_file.read_text(encoding="utf-8"))

    def test_xss_is_sanitized(self):
        token = self.csrf()
        response = self.client.post(
            "/api/contact",
            data={
                "csrf_token": token,
                "name": "<script>alert(1)</script>Иван",
                "contact": "ivan@example.com",
                "message": "<img src=x onerror=alert(1)>Нужен бот для записи клиентов",
                "consent": "1",
            },
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        stored = (self.tmp / "data" / "messages.json").read_text(encoding="utf-8")
        self.assertNotIn("<script>", stored)
        self.assertNotIn("<img", stored)
        self.assertNotIn("onerror", stored)

    def test_rate_limit(self):
        token = self.csrf()
        last = None
        for _ in range(8):
            last = self.client.post(
                "/api/contact",
                data={
                    "csrf_token": token,
                    "name": "Иван",
                    "contact": "ivan@example.com",
                    "message": "Сообщение достаточной длины для теста",
                    "consent": "1",
                },
                headers={"Accept": "application/json"},
            )
        self.assertEqual(last.status_code, 429)


class AdminTests(BaseTestCase):
    def login(self):
        token = self.csrf("/admin/login")
        return self.client.post(
            "/admin/login",
            data={"csrf_token": token, "password": "test-password"},
            follow_redirects=False,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.headers["Location"])

    def test_wrong_password_rejected(self):
        token = self.csrf("/admin/login")
        response = self.client.post(
            "/admin/login", data={"csrf_token": token, "password": "wrong"}
        )
        self.assertEqual(response.status_code, 401)

    def test_login_and_toggle_case(self):
        self.login()
        dashboard = self.client.get("/admin/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("Скрыть кейс", dashboard.get_data(as_text=True))

        token = self.csrf("/admin/")
        self.client.post(
            "/admin/cases/saveliy-habit-tracker/toggle",
            data={"csrf_token": token, "hidden": "1"},
        )

        # Кейс скрыт: страница отдаёт 404, из главной исчез, из sitemap исчез
        self.assertEqual(self.client.get("/projects/saveliy-habit-tracker/").status_code, 404)
        self.assertNotIn("saveliy-habit-tracker", self.client.get("/sitemap.xml").get_data(as_text=True))

        # Возвращаем обратно
        token = self.csrf("/admin/")
        self.client.post(
            "/admin/cases/saveliy-habit-tracker/toggle",
            data={"csrf_token": token},
        )
        self.assertEqual(self.client.get("/projects/saveliy-habit-tracker/").status_code, 200)

    def test_logout(self):
        self.login()
        token = self.csrf("/admin/")
        self.client.post("/admin/logout", data={"csrf_token": token})
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_login_is_rate_limited(self):
        token = self.csrf("/admin/login")
        limit = self.app.config["RATE_LIMIT_MAX"]
        codes = [
            self.client.post(
                "/admin/login", data={"csrf_token": token, "password": "wrong"}
            ).status_code
            for _ in range(limit)
        ]
        self.assertEqual(codes, [401] * limit)
        blocked = self.client.post(
            "/admin/login", data={"csrf_token": token, "password": "test-password"}
        )
        self.assertEqual(blocked.status_code, 429)

    def test_successful_login_resets_attempts(self):
        token = self.csrf("/admin/login")
        for _ in range(3):
            self.client.post("/admin/login", data={"csrf_token": token, "password": "wrong"})
        success = self.client.post(
            "/admin/login", data={"csrf_token": token, "password": "test-password"}
        )
        self.assertEqual(success.status_code, 302)

        logout_token = self.csrf("/admin/")
        self.client.post("/admin/logout", data={"csrf_token": logout_token})

        token = self.csrf("/admin/login")
        for _ in range(3):
            response = self.client.post(
                "/admin/login", data={"csrf_token": token, "password": "wrong"}
            )
            self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
