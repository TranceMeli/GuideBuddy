from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Guide, Profile, Report, Step
from .permissions import MODERATOR_GROUP, write_denial

PASSWORD = "sehr-sicher-9876"


class ModerationBase(APITestCase):
    def setUp(self):
        cache.clear()
        self.guide = Guide.objects.create(title="Python einrichten", summary="Kurz")
        Step.objects.create(guide=self.guide, order=1, title="Ordner", body="x")
        self.user = User.objects.create_user("mel", password=PASSWORD)
        self.mod = User.objects.create_user("mod", password=PASSWORD)
        self.mod.groups.add(Group.objects.get(name=MODERATOR_GROUP))

    def as_user(self, user):
        token = self.client.post(
            "/api/auth/login/", {"username": user.username, "password": PASSWORD}, format="json"
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def put(self, title="Neu"):
        return self.client.put("/api/guides/python-einrichten/", {"title": title}, format="json")


class NewAccountTests(ModerationBase):
    @override_settings(NEW_ACCOUNT_WAIT_HOURS=24)
    def test_new_accounts_must_wait_before_writing(self):
        Profile.objects.create(user=self.user, email_verified_at=timezone.now() - timedelta(hours=2))
        self.as_user(self.user)
        denied = self.client.post("/api/guides/", {"title": "Zu früh"}, format="json")
        self.assertEqual(denied.status_code, 403)
        self.assertIn("24 hours", denied.data["detail"])
        self.assertEqual(self.put().status_code, 403)
        self.assertEqual(self.client.get("/api/auth/me/").data["can_write"], False)

        Profile.objects.filter(user=self.user).update(
            email_verified_at=timezone.now() - timedelta(hours=25)
        )
        self.assertEqual(self.client.post("/api/guides/", {"title": "Jetzt"}, format="json").status_code, 201)

    @override_settings(NEW_ACCOUNT_WAIT_HOURS=24)
    def test_moderators_and_old_accounts_are_exempt(self):
        # Account without profile, old enough via date_joined
        User.objects.filter(pk=self.user.pk).update(date_joined=timezone.now() - timedelta(days=3))
        self.user.refresh_from_db()
        self.assertIsNone(write_denial(self.user))
        # Moderator frisch angelegt
        self.assertIsNone(write_denial(self.mod))


class LockTests(ModerationBase):
    def test_locked_guide_can_only_be_edited_by_moderators(self):
        self.as_user(self.mod)
        locked = self.client.post("/api/guides/python-einrichten/lock/")
        self.assertEqual(locked.status_code, 200)
        self.assertTrue(locked.data["is_locked"])
        self.assertTrue(self.client.get("/api/guides/python-einrichten/").data["is_locked"])
        self.assertEqual(self.put("Vom Moderator").status_code, 200)

        self.as_user(self.user)
        denied = self.put("Vom Nutzer")
        self.assertEqual(denied.status_code, 403)
        self.assertIn("locked", denied.data["detail"])
        self.guide.refresh_from_db()
        self.assertEqual(self.guide.title, "Vom Moderator")
        # Everybody can still read, and create other guides
        self.assertEqual(self.client.get("/api/guides/python-einrichten/").status_code, 200)
        self.assertEqual(self.client.post("/api/guides/", {"title": "Anderer"}, format="json").status_code, 201)

        self.as_user(self.mod)
        unlocked = self.client.post("/api/guides/python-einrichten/unlock/")
        self.assertFalse(unlocked.data["is_locked"])
        self.as_user(self.user)
        self.assertEqual(self.put("Wieder frei").status_code, 200)

    def test_only_moderators_can_lock(self):
        self.assertEqual(self.client.post("/api/guides/python-einrichten/lock/").status_code, 401)
        self.as_user(self.user)
        self.assertEqual(self.client.post("/api/guides/python-einrichten/lock/").status_code, 403)
        self.guide.refresh_from_db()
        self.assertFalse(self.guide.is_locked)

    def test_lock_is_recorded_in_history(self):
        self.as_user(self.mod)
        self.client.post("/api/guides/python-einrichten/lock/")
        entry = self.client.get("/api/guides/python-einrichten/history/").data["guide"][0]
        self.assertEqual(entry["reason"], "Guide locked")
        self.assertEqual(entry["user"], "mod")


class ReportTests(ModerationBase):
    def report(self, **data):
        payload = {"reason": "spam", "comment": "Werbung"}
        payload.update(data)
        return self.client.post("/api/guides/python-einrichten/report/", payload, format="json")

    def test_reporting_requires_login_and_valid_reason(self):
        self.assertEqual(self.report().status_code, 401)
        self.as_user(self.user)
        self.assertEqual(self.report(reason="quatsch").status_code, 400)
        self.assertEqual(self.report().status_code, 201)

    def test_one_open_report_per_user_and_guide(self):
        self.as_user(self.user)
        self.report()
        again = self.report(comment="nochmal")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(Report.objects.count(), 1)

    def test_moderators_review_and_resolve_reports(self):
        self.as_user(self.user)
        self.report()
        self.assertEqual(self.client.get("/api/reports/").status_code, 403)

        self.as_user(self.mod)
        listing = self.client.get("/api/reports/").data
        self.assertEqual(listing["count"], 1)
        item = listing["results"][0]
        self.assertEqual(item["guide"], "python-einrichten")
        self.assertEqual(item["reporter"], "mel")
        self.assertEqual(item["reason_label"], "Spam or advertising")

        done = self.client.post(f"/api/reports/{item['id']}/resolve/", {"note": "Ist ok"}, format="json")
        self.assertEqual(done.status_code, 200)
        self.assertEqual(done.data["resolved_by"], "mod")
        self.assertEqual(self.client.get("/api/reports/").data["count"], 0)
        self.assertEqual(self.client.get("/api/reports/", {"status": "resolved"}).data["count"], 1)
        # After resolving, it may be reported again
        self.as_user(self.user)
        self.assertEqual(self.report().status_code, 201)

    def test_reports_are_anonymous_to_others_and_survive_account_deletion(self):
        self.as_user(self.user)
        self.report()
        self.client.delete("/api/auth/account/", {"password": PASSWORD}, format="json")
        report = Report.objects.get()
        self.assertIsNone(report.reporter)

    def test_reporting_is_throttled(self):
        self.as_user(self.user)
        for i in range(10):
            Report.objects.filter(reporter=self.user).delete()
            self.assertEqual(self.report(comment=str(i)).status_code, 201)
        Report.objects.filter(reporter=self.user).delete()
        self.assertEqual(self.report().status_code, 429)


class TemplateVersionTests(TestCase):
    """The old Django pages must not bypass the new rules."""

    def setUp(self):
        self.guide = Guide.objects.create(title="Gesperrt", is_locked=True)
        self.user = User.objects.create_user("mel", password=PASSWORD)
        self.mod = User.objects.create_user("mod", password=PASSWORD)
        self.mod.groups.add(Group.objects.get(name=MODERATOR_GROUP))

    def test_locked_guide_cannot_be_edited_via_django_page(self):
        url = reverse("guides:edit", args=[self.guide.slug])
        self.client.login(username="mel", password=PASSWORD)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"title": "Hack"}).status_code, 403)
        self.guide.refresh_from_db()
        self.assertEqual(self.guide.title, "Gesperrt")
        self.client.login(username="mod", password=PASSWORD)
        self.assertEqual(self.client.get(url).status_code, 200)

    @override_settings(NEW_ACCOUNT_WAIT_HOURS=24)
    def test_new_account_cannot_create_via_django_page(self):
        Profile.objects.create(user=self.user, email_verified_at=timezone.now())
        self.client.login(username="mel", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("guides:create")).status_code, 403)

    @override_settings(FRONTEND_URL="https://buddy.example")
    def test_old_registration_redirects_to_the_new_frontend(self):
        response = self.client.get(reverse("register"))
        self.assertRedirects(response, "https://buddy.example/registrieren", fetch_redirect_response=False)

    def test_django_password_reset_pages_are_gone(self):
        self.assertEqual(self.client.get("/accounts/password_reset/").status_code, 404)
