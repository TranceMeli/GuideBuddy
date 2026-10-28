import re
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

from . import captcha
from .models import Guide, Profile, Step

PASSWORD = "sehr-sicher-9876"


def register_payload(**overrides):
    payload = {
        "username": "neu",
        "email": "neu@example.org",
        "password": PASSWORD,
        "accept_terms": True,
    }
    payload.update(overrides)
    return payload


def link_params(message):
    """Get uid and token from the link in an e-mail."""
    match = re.search(r"\?uid=([^&\s]+)&token=([^\s]+)", message.body)
    assert match, message.body
    return {"uid": match.group(1), "token": match.group(2)}


class RegistrationTests(APITestCase):
    def setUp(self):
        cache.clear()

    def register(self, **overrides):
        return self.client.post("/api/auth/register/", register_payload(**overrides), format="json")

    def test_register_creates_inactive_account_and_mails_a_link(self):
        response = self.register()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn("token", response.data)
        user = User.objects.get(username="neu")
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.profile.terms_accepted_at)
        self.assertIsNone(user.profile.email_verified_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["neu@example.org"])
        self.assertIn("/confirm?uid=", mail.outbox[0].body)

    def test_cannot_log_in_before_confirming_then_can(self):
        self.register()
        login = {"username": "neu", "password": PASSWORD}
        before = self.client.post("/api/auth/login/", login, format="json")
        self.assertEqual(before.status_code, 400)
        self.assertEqual(before.data["code"], "email_not_verified")

        params = link_params(mail.outbox[0])
        verified = self.client.post("/api/auth/verify/", params, format="json")
        self.assertEqual(verified.status_code, 200, verified.data)
        user = User.objects.get(username="neu")
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.profile.email_verified_at)

        after = self.client.post("/api/auth/login/", login, format="json")
        self.assertEqual(after.status_code, 200)
        self.assertEqual(after.data["user"]["username"], "neu")
        self.assertIn("access", after.data)

        # The link only works once
        again = self.client.post("/api/auth/verify/", params, format="json")
        self.assertEqual(again.status_code, 400)

    def test_wrong_password_and_unknown_user_look_the_same(self):
        User.objects.create_user("mel", password=PASSWORD)
        wrong = self.client.post("/api/auth/login/", {"username": "mel", "password": "falsch"}, format="json")
        unknown = self.client.post("/api/auth/login/", {"username": "nobody", "password": "x"}, format="json")
        self.assertEqual(wrong.status_code, 400)
        self.assertEqual(wrong.data, unknown.data)

    def test_tampered_or_foreign_link_is_rejected(self):
        self.register()
        params = link_params(mail.outbox[0])
        bad = self.client.post("/api/auth/verify/", {**params, "token": "abc-123"}, format="json")
        self.assertEqual(bad.status_code, 400)
        garbage = self.client.post("/api/auth/verify/", {"uid": "!!", "token": "x"}, format="json")
        self.assertEqual(garbage.status_code, 400)
        self.assertFalse(User.objects.get(username="neu").is_active)

    def test_validation(self):
        self.assertEqual(self.register(accept_terms=False).status_code, 400)
        weak = self.register(password="123")
        self.assertEqual(weak.status_code, 400)
        self.assertIn("password", weak.data)
        self.assertEqual(self.register(email="keine-mail").status_code, 400)
        self.assertEqual(self.register().status_code, 201)
        duplicate = self.register(username="NEU", email="andere@example.org")
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("username", duplicate.data)

    def test_existing_email_gets_same_answer_and_a_notice(self):
        User.objects.create_user("mel", email="mel@example.org", password=PASSWORD)
        fresh = self.register(username="eins", email="eins@example.org")
        mail.outbox.clear()
        taken = self.register(username="zwei", email="MEL@example.org")
        self.assertEqual(taken.status_code, 201)
        self.assertEqual(taken.data, fresh.data)  # does not reveal whether the address exists
        self.assertFalse(User.objects.filter(username="zwei").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("already", mail.outbox[0].subject)

    def test_honeypot_pretends_success_but_creates_nothing(self):
        response = self.register(website="http://spam.example")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(User.objects.filter(username="neu").exists())
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(TURNSTILE_SECRET_KEY="geheim")
    def test_captcha_is_enforced_when_configured(self):
        self.assertEqual(self.register().status_code, 400)  # no token
        with mock.patch("guides.api.views.verify_captcha", return_value=False):
            self.assertEqual(self.register(captcha_token="x").status_code, 400)
        with mock.patch("guides.api.views.verify_captcha", return_value=True):
            self.assertEqual(self.register(captcha_token="x").status_code, 201)

    @override_settings(TURNSTILE_SECRET_KEY="geheim")
    def test_captcha_verification_calls_cloudflare(self):
        self.assertFalse(captcha.verify_captcha(""))  # without a token, do not even ask
        ok = mock.MagicMock()
        ok.__enter__.return_value.read.return_value = b'{"success": true}'
        with mock.patch("guides.captcha.urllib.request.urlopen", return_value=ok) as opened:
            self.assertTrue(captcha.verify_captcha("token", "1.2.3.4"))
        sent = opened.call_args.args[0].data.decode()
        self.assertIn("secret=geheim", sent)
        self.assertIn("response=token", sent)
        with mock.patch("guides.captcha.urllib.request.urlopen", side_effect=OSError("offline")):
            with self.assertLogs("guides.captcha", level="ERROR"):
                self.assertFalse(captcha.verify_captcha("token"))  # reject on errors

    @override_settings(TURNSTILE_SECRET_KEY="")
    def test_captcha_is_off_without_secret(self):
        self.assertTrue(captcha.verify_captcha(""))

    def test_registration_is_throttled(self):
        for i in range(10):
            self.register(username=f"u{i}", email=f"u{i}@example.org")
        self.assertEqual(self.register(username="u11", email="u11@example.org").status_code, 429)


class ResendAndResetTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client.post("/api/auth/register/", register_payload(), format="json")
        self.pending_mail = mail.outbox[0]
        mail.outbox.clear()
        self.active = User.objects.create_user("mel", email="mel@example.org", password=PASSWORD)

    def test_resend_only_mails_unconfirmed_accounts(self):
        known = self.client.post("/api/auth/resend/", {"email": "neu@example.org"}, format="json")
        self.assertEqual(len(mail.outbox), 1)
        mail.outbox.clear()
        unknown = self.client.post("/api/auth/resend/", {"email": "wer@example.org"}, format="json")
        active = self.client.post("/api/auth/resend/", {"email": "mel@example.org"}, format="json")
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(known.data, unknown.data)
        self.assertEqual(known.data, active.data)

    def test_password_reset_flow(self):
        self.client.post("/api/auth/password-reset/", {"email": "mel@example.org"}, format="json")
        self.assertEqual(len(mail.outbox), 1)
        params = link_params(mail.outbox[0])
        self.assertIn("/reset-password?uid=", mail.outbox[0].body)

        old_token = self.client.post(
            "/api/auth/login/", {"username": "mel", "password": PASSWORD}, format="json"
        ).data["access"]

        weak = self.client.post("/api/auth/password-reset/confirm/", {**params, "password": "123"}, format="json")
        self.assertEqual(weak.status_code, 400)
        self.assertIn("password", weak.data)

        done = self.client.post(
            "/api/auth/password-reset/confirm/", {**params, "password": "ganz-neu-4711x"}, format="json"
        )
        self.assertEqual(done.status_code, 200, done.data)
        login = self.client.post("/api/auth/login/", {"username": "mel", "password": "ganz-neu-4711x"}, format="json")
        self.assertEqual(login.status_code, 200)
        # Old logins are invalid, the link can be used only once
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {old_token}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
        self.client.credentials()
        again = self.client.post(
            "/api/auth/password-reset/confirm/", {**params, "password": "nochmal-5555y"}, format="json"
        )
        self.assertEqual(again.status_code, 400)

    def test_reset_request_does_not_reveal_accounts(self):
        known = self.client.post("/api/auth/password-reset/", {"email": "mel@example.org"}, format="json")
        mail.outbox.clear()
        unknown = self.client.post("/api/auth/password-reset/", {"email": "wer@example.org"}, format="json")
        unconfirmed = self.client.post("/api/auth/password-reset/", {"email": "neu@example.org"}, format="json")
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(known.data, unknown.data)
        self.assertEqual(known.data, unconfirmed.data)

    def test_mail_requests_are_throttled(self):
        for _ in range(5):
            self.client.post("/api/auth/password-reset/", {"email": "mel@example.org"}, format="json")
        blocked = self.client.post("/api/auth/password-reset/", {"email": "mel@example.org"}, format="json")
        self.assertEqual(blocked.status_code, 429)


class AccountTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("mel", email="mel@example.org", password=PASSWORD)
        token = self.client.post("/api/auth/login/", {"username": "mel", "password": PASSWORD}, format="json").data[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_me_describes_the_user(self):
        data = self.client.get("/api/auth/me/").data
        self.assertEqual(data["username"], "mel")
        self.assertFalse(data["is_moderator"])
        self.assertTrue(data["can_write"])

    def test_delete_account_keeps_content_without_the_name(self):
        guide = Guide.objects.create(title="Mein Guide", created_by=self.user)
        Step.objects.create(guide=guide, order=1, title="Eins", body="x")
        self.client.put("/api/guides/mein-guide/", {"title": "Mein Guide 2"}, format="json")
        self.assertTrue(guide.history.filter(history_user=self.user).exists())

        wrong = self.client.delete("/api/auth/account/", {"password": "falsch"}, format="json")
        self.assertEqual(wrong.status_code, 400)
        self.assertTrue(User.objects.filter(username="mel").exists())

        done = self.client.delete("/api/auth/account/", {"password": PASSWORD}, format="json")
        self.assertEqual(done.status_code, 204)
        self.assertFalse(User.objects.filter(username="mel").exists())
        guide.refresh_from_db()
        self.assertIsNone(guide.created_by)
        self.assertFalse(guide.history.filter(history_user__isnull=False).exists())
        self.assertEqual(Profile.objects.count(), 0)

    def test_admin_accounts_cannot_be_deleted_here(self):
        User.objects.filter(pk=self.user.pk).update(is_staff=True)
        response = self.client.delete("/api/auth/account/", {"password": PASSWORD}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.filter(username="mel").exists())

    def test_banned_account_cannot_log_in_or_confirm(self):
        banned = User.objects.create_user("boese", email="b@example.org", password=PASSWORD, is_active=False)
        from django.utils import timezone

        Profile.objects.create(user=banned, banned_at=timezone.now())
        login = self.client.post("/api/auth/login/", {"username": "boese", "password": PASSWORD}, format="json")
        self.assertEqual(login.status_code, 403)
        self.assertEqual(login.data["code"], "banned")

        from .tokens import email_verification_token, encode_uid

        params = {"uid": encode_uid(banned), "token": email_verification_token.make_token(banned)}
        verify = self.client.post("/api/auth/verify/", params, format="json")
        self.assertEqual(verify.status_code, 400)
        banned.refresh_from_db()
        self.assertFalse(banned.is_active)

    def test_stale_token_does_not_block_public_reading(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer abgelaufen")
        self.assertEqual(self.client.get("/api/guides/").status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
        self.assertEqual(self.client.post("/api/guides/", {"title": "x"}, format="json").status_code, 401)


class ReadableConsoleBackendTests(APITestCase):
    def test_link_is_printed_unencoded(self):
        import io

        from django.core.mail import EmailMessage

        from guides.mail_backend import ReadableConsoleEmailBackend

        link = "http://localhost:3000/confirm?uid=MQ&token=abc-" + "x" * 90
        stream = io.StringIO()
        backend = ReadableConsoleEmailBackend(stream=stream)
        backend.send_messages(
            [EmailMessage("Betreff äöü", f"Hallo\n{link}\n", "a@b.de", ["c@d.de"])]
        )
        out = stream.getvalue()
        self.assertIn(link, out)
        self.assertIn("Betreff äöü", out)
        self.assertNotIn("=3D", out)
