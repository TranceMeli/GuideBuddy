from datetime import timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import Profile

PASSWORD = "sehr-geheim-4711"


class JWTTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("mel", email="mel@example.org", password=PASSWORD)
        Profile.objects.create(user=self.user)

    def login(self):
        response = self.client.post(
            "/api/auth/login/", {"username": "mel", "password": PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        return response.data

    def bearer(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def me(self, token):
        self.bearer(token)
        status = self.client.get("/api/auth/me/").status_code
        self.client.credentials()
        return status

    def refresh(self, token):
        return self.client.post("/api/auth/refresh/", {"refresh": token}, format="json")

    def test_login_returns_tokens_and_user(self):
        data = self.login()
        self.assertEqual(set(data), {"access", "refresh", "user"})
        self.assertEqual(self.me(data["access"]), 200)
        # The refresh token is not an access token
        self.assertEqual(self.me(data["refresh"]), 401)

    def test_access_token_is_short_lived(self):
        data = self.login()
        token = AccessToken(data["access"])
        self.assertLessEqual(token["exp"] - token["iat"], 15 * 60)

    def test_expired_access_token_is_rejected(self):
        # Expired: writing and /me fail, reading stays public
        token = AccessToken.for_user(self.user)
        token.set_exp(from_time=timezone.now() - timedelta(hours=1), lifetime=timedelta(minutes=10))
        self.bearer(str(token))
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
        self.assertEqual(self.client.post("/api/guides/", {"title": "x"}, format="json").status_code, 401)
        self.assertEqual(self.client.get("/api/guides/").status_code, 200)

    def test_tampered_token_is_rejected(self):
        data = self.login()
        head, payload, signature = data["access"].split(".")
        self.assertEqual(self.me(f"{head}.{payload}.{signature[:-3]}abc"), 401)
        self.assertEqual(self.me(f"{head}.{payload}"), 401)

    def test_refresh_rotates_and_old_token_is_dead(self):
        data = self.login()
        first = self.refresh(data["refresh"])
        self.assertEqual(first.status_code, 200)
        self.assertNotEqual(first.data["refresh"], data["refresh"])
        self.assertEqual(self.me(first.data["access"]), 200)
        # Reusing the old refresh token fails
        self.assertEqual(self.refresh(data["refresh"]).status_code, 401)
        # Der neue funktioniert weiter
        self.assertEqual(self.refresh(first.data["refresh"]).status_code, 200)

    def test_access_token_cannot_be_used_to_refresh(self):
        data = self.login()
        self.assertEqual(self.refresh(data["access"]).status_code, 401)
        self.assertEqual(self.refresh("kaputt").status_code, 401)

    def test_logout_revokes_refresh_token(self):
        data = self.login()
        out = self.client.post("/api/auth/logout/", {"refresh": data["refresh"]}, format="json")
        self.assertEqual(out.status_code, 204)
        self.assertEqual(self.refresh(data["refresh"]).status_code, 401)
        # Logout without or with a broken token is harmless
        self.assertEqual(self.client.post("/api/auth/logout/", {}, format="json").status_code, 204)
        self.assertEqual(
            self.client.post("/api/auth/logout/", {"refresh": "kaputt"}, format="json").status_code, 204
        )

    def test_password_change_revokes_all_tokens(self):
        data = self.login()
        self.user.set_password("ganz-neu-9876x")
        self.user.save()
        self.assertEqual(self.me(data["access"]), 401)
        self.assertEqual(self.refresh(data["refresh"]).status_code, 401)

    def test_banned_user_loses_access_immediately(self):
        data = self.login()
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.me(data["access"]), 401)
        self.assertEqual(self.refresh(data["refresh"]).status_code, 401)

    def test_deleted_user_cannot_refresh(self):
        data = self.login()
        self.user.delete()
        self.assertEqual(self.refresh(data["refresh"]).status_code, 401)

    def test_refresh_is_throttled(self):
        for _ in range(30):
            self.refresh("kaputt")
        self.assertEqual(self.refresh("kaputt").status_code, 429)

    def test_old_drf_token_header_no_longer_works(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token abc")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
