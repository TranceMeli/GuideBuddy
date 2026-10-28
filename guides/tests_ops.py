import email
import email.policy
import io
import json
import os
import socketserver
import sqlite3
import subprocess
import sys
import tempfile
import threading
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Profile


class BackupTests(TestCase):
    def test_backup_is_consistent_and_old_ones_are_pruned(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "live.sqlite3"
            conn = sqlite3.connect(source)
            conn.execute("create table guide (title text)")
            conn.execute("insert into guide values ('Python einrichten')")
            conn.commit()
            conn.close()

            target_dir = tmp / "backups"
            target_dir.mkdir()
            for day in ("20200101", "20200102", "20200103"):
                (target_dir / f"db-{day}-000000.sqlite3").write_bytes(b"alt")

            call_command(
                "backup_db", source=str(source), target_dir=str(target_dir), keep=2, stdout=io.StringIO()
            )

            files = sorted(target_dir.glob("db-*.sqlite3"))
            self.assertEqual(len(files), 2)
            newest = files[-1]
            self.assertFalse(newest.name.startswith("db-2020"))  # the new one stays
            self.assertEqual(files[0].name, "db-20200103-000000.sqlite3")
            check = sqlite3.connect(newest)
            self.assertEqual(check.execute("select title from guide").fetchall(), [("Python einrichten",)])
            check.close()

    def test_backup_fails_clearly_without_database_file(self):
        with self.assertRaises(CommandError):
            call_command("backup_db", source="/gibt/es/nicht.sqlite3", verbosity=0)


class CleanupTests(TestCase):
    def make(self, name, *, active, days_old, verified=False, banned=False, profile=True, superuser=False):
        user = User.objects.create_user(name, password="x", is_active=active, is_superuser=superuser)
        User.objects.filter(pk=user.pk).update(date_joined=timezone.now() - timedelta(days=days_old))
        if profile:
            Profile.objects.create(
                user=user,
                email_verified_at=timezone.now() if verified else None,
                banned_at=timezone.now() if banned else None,
            )
        return user

    def test_only_stale_unconfirmed_registrations_are_deleted(self):
        self.make("alt_unbestaetigt", active=False, days_old=5)
        self.make("frisch_unbestaetigt", active=False, days_old=1)
        self.make("alt_aktiv", active=True, days_old=5, verified=True)
        self.make("alt_deaktiviert_aber_bestaetigt", active=False, days_old=5, verified=True)
        self.make("alt_gesperrt", active=False, days_old=5, banned=True)
        self.make("alt_ohne_profil", active=False, days_old=5, profile=False)
        self.make("alt_admin", active=False, days_old=5, superuser=True)

        call_command("cleanup_unverified", days=3, stdout=io.StringIO())

        remaining = set(User.objects.values_list("username", flat=True))
        self.assertNotIn("alt_unbestaetigt", remaining)
        self.assertEqual(
            remaining,
            {
                "frisch_unbestaetigt",
                "alt_aktiv",
                "alt_deaktiviert_aber_bestaetigt",
                "alt_gesperrt",
                "alt_ohne_profil",
                "alt_admin",
            },
        )


class SettingsTests(TestCase):
    """In production (DJANGO_DEBUG=0) the server must not start with insecure defaults."""

    SCRIPT = (
        "import django, json; django.setup(); from django.conf import settings as s; "
        "print(json.dumps({'debug': s.DEBUG, 'secure_cookie': s.SESSION_COOKIE_SECURE, "
        "'wait': s.NEW_ACCOUNT_WAIT_HOURS, "
        "'whitenoise': 'whitenoise.middleware.WhiteNoiseMiddleware' in s.MIDDLEWARE, "
        "'mailer': s.MAILERS['default']}))"
    )

    def run_settings(self, **env):
        full_env = {**os.environ, "DJANGO_SETTINGS_MODULE": "backend.settings"}
        for key in ("DJANGO_DEBUG", "DJANGO_SECRET_KEY", "EMAIL_HOST", "EMAIL_USE_SSL", "EMAIL_PORT"):
            full_env.pop(key, None)
        full_env.update(env)
        return subprocess.run(
            [sys.executable, "-c", self.SCRIPT],
            cwd=settings.BASE_DIR,
            env=full_env,
            capture_output=True,
            text=True,
        )

    def test_production_requires_a_secret_key(self):
        result = self.run_settings(DJANGO_DEBUG="0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_production_uses_secure_defaults(self):
        result = self.run_settings(DJANGO_DEBUG="0", DJANGO_SECRET_KEY="x" * 60)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(
            (data["debug"], data["secure_cookie"], data["wait"], data["whitenoise"]),
            (False, True, 24, True),
        )

    def test_development_needs_no_configuration(self):
        result = self.run_settings()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(
            (data["debug"], data["secure_cookie"], data["wait"], data["whitenoise"]),
            (True, False, 0, False),
        )
        self.assertTrue(data["mailer"]["BACKEND"].endswith("ReadableConsoleEmailBackend"))

    def test_smtp_is_configured_from_environment(self):
        result = self.run_settings(
            EMAIL_HOST="smtp.example.org", EMAIL_HOST_USER="user", EMAIL_HOST_PASSWORD="pw"
        )
        options = json.loads(result.stdout)["mailer"]["OPTIONS"]
        self.assertEqual(
            (options["host"], options["port"], options["use_tls"], options["use_ssl"]),
            ("smtp.example.org", 587, True, False),
        )
        ssl = json.loads(self.run_settings(EMAIL_HOST="h", EMAIL_USE_SSL="true").stdout)["mailer"]["OPTIONS"]
        self.assertEqual((ssl["port"], ssl["use_tls"], ssl["use_ssl"]), (465, False, True))


class _SmtpHandler(socketserver.StreamRequestHandler):
    """Tiny SMTP server that accepts e-mails (for the sending test)."""

    def handle(self):
        write = lambda text: self.wfile.write((text + "\r\n").encode())
        write("220 test ESMTP")
        in_data, body = False, []
        for raw in self.rfile:
            line = raw.decode().rstrip("\r\n")
            if in_data:
                if line == ".":
                    in_data = False
                    self.server.messages.append("\n".join(body))
                    write("250 queued")
                else:
                    body.append(line)
                continue
            command = line.upper()
            if command.startswith("EHLO") or command.startswith("HELO"):
                write("250 test")
            elif command.startswith("DATA"):
                in_data = True
                write("354 go")
            elif command.startswith("QUIT"):
                write("221 bye")
                return
            else:
                write("250 ok")


class SmtpDeliveryTests(TestCase):
    def test_mail_reaches_an_smtp_server_with_the_configured_options(self):
        server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _SmtpHandler)
        server.messages = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            smtp = {
                "default": {
                    "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
                    "OPTIONS": {"host": "127.0.0.1", "port": server.server_address[1], "timeout": 5},
                }
            }
            with override_settings(MAILERS=smtp):
                from .mails import send_password_reset_mail

                user = User.objects.create_user("mel", email="mel@example.org", password="x")
                send_password_reset_mail(user)
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(len(server.messages), 1)
        # Read it like a mail client: subject and body are encoded (umlauts, long lines)
        message = email.message_from_string(server.messages[0], policy=email.policy.default)
        self.assertEqual(message["Subject"], "Reset your password")
        self.assertEqual(message["To"], "mel@example.org")
        self.assertIn("/reset-password?uid=", message.get_content())


class SeedSamplesTests(TestCase):
    """seed_samples creates the sample guide, once."""

    def test_sample_is_created_once(self):
        from guides.models import Guide

        out = io.StringIO()
        call_command("seed_samples", stdout=out)
        guide = Guide.objects.get()
        self.assertEqual(guide.guide_type, "page")
        self.assertEqual(guide.elements.filter(kind="step").count(), 3)
        call_command("seed_samples", stdout=out)
        self.assertEqual(Guide.objects.count(), 1)
        self.assertIn("exists:", out.getvalue())
