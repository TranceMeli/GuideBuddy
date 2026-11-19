from django.contrib.auth.models import Group, User
from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import Category, Guide, GuideComment, GuideStatus, Report
from .permissions import MODERATOR_GROUP

PASSWORD = "sehr-sicher-9876"


class LifecycleBase(APITestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name="Computers")
        self.author = User.objects.create_user("anna", password=PASSWORD)
        self.reader = User.objects.create_user("tom", password=PASSWORD)
        self.mod = User.objects.create_user("mod", password=PASSWORD)
        self.mod.groups.add(Group.objects.get(name=MODERATOR_GROUP))
        self.guide = Guide.objects.create(title="Install Python", category=self.category, created_by=self.author)

    def as_user(self, user):
        token = self.client.post(
            "/api/auth/login/", {"username": user.username, "password": PASSWORD}, format="json"
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def url(self, path=""):
        return f"/api/guides/{self.guide.slug}/{path}"


class StatusTests(LifecycleBase):
    def test_a_new_guide_is_published(self):
        self.assertEqual(self.client.get(self.url()).data["status"], "published")

    def test_the_author_archives_and_restores(self):
        self.as_user(self.author)
        self.assertEqual(self.client.post(self.url("archive/")).data["status"], "archived")
        self.assertEqual(self.client.post(self.url("restore/")).data["status"], "published")

    def test_a_moderator_may_archive_but_another_reader_may_not(self):
        self.as_user(self.reader)
        self.assertEqual(self.client.post(self.url("archive/")).status_code, 403)
        self.as_user(self.mod)
        self.assertEqual(self.client.post(self.url("archive/")).status_code, 200)

    def test_an_archived_guide_leaves_the_overview_but_its_link_works(self):
        Guide.objects.filter(pk=self.guide.pk).update(status=GuideStatus.ARCHIVED)
        self.assertEqual(self.client.get("/api/guides/").data["count"], 0)
        self.assertEqual(self.client.get("/api/guides/?q=Python").data["count"], 0)
        self.assertEqual(self.client.get(self.url()).data["status"], "archived")

    def test_a_status_change_is_not_an_edit(self):
        before = self.client.get(self.url()).data
        self.as_user(self.mod)
        self.client.post(self.url("archive/"))
        self.client.post(self.url("restore/"))
        after = self.client.get(self.url()).data
        self.assertEqual((after["version"], after["contributors"], after["updated_at"]), (before["version"], [], before["updated_at"]))

    def test_archiving_is_recorded_in_the_history(self):
        self.as_user(self.author)
        self.client.post(self.url("archive/"))
        self.assertEqual(self.guide.history.first().history_change_reason, "Guide archived")

    def test_anyone_who_may_edit_marks_a_guide_as_outdated_and_current(self):
        self.as_user(self.reader)
        self.assertEqual(self.client.post(self.url("mark-outdated/")).data["status"], "outdated")
        self.assertEqual(self.client.post(self.url("mark-current/")).data["status"], "published")

    def test_a_locked_guide_can_only_be_marked_by_moderators(self):
        Guide.objects.filter(pk=self.guide.pk).update(is_locked=True)
        self.as_user(self.reader)
        self.assertEqual(self.client.post(self.url("mark-outdated/")).status_code, 403)
        self.as_user(self.mod)
        self.assertEqual(self.client.post(self.url("mark-outdated/")).status_code, 200)

    def test_an_archived_guide_cannot_be_marked_outdated(self):
        Guide.objects.filter(pk=self.guide.pk).update(status=GuideStatus.ARCHIVED)
        self.as_user(self.author)
        self.assertEqual(self.client.post(self.url("mark-outdated/")).status_code, 400)

    def test_the_status_cannot_be_set_by_saving_the_guide(self):
        self.as_user(self.author)
        self.client.put(self.url(), {"title": "Install Python", "status": "archived"}, format="json")
        self.guide.refresh_from_db()
        self.assertEqual(self.guide.status, "published")

    def test_visitors_cannot_change_the_status(self):
        self.assertEqual(self.client.post(self.url("archive/")).status_code, 401)


class TrustDetailsTests(LifecycleBase):
    def test_version_counts_the_saved_changes(self):
        before = self.client.get(self.url()).data["version"]
        self.as_user(self.author)
        self.client.put(self.url(), {"title": "Install Python 3"}, format="json")
        self.assertEqual(self.client.get(self.url()).data["version"], before + 1)

    def test_contributors_are_the_other_editors(self):
        self.as_user(self.reader)
        self.client.put(self.url(), {"title": "Install Python 3"}, format="json")
        self.assertEqual(self.client.get(self.url()).data["contributors"], ["tom"])

    def test_the_author_is_not_listed_as_contributor(self):
        self.as_user(self.author)
        self.client.put(self.url(), {"title": "Install Python 3"}, format="json")
        self.assertEqual(self.client.get(self.url()).data["contributors"], [])

    def test_open_outdated_reports_are_counted(self):
        Report.objects.create(guide=self.guide, reporter=self.reader, reason=Report.Reason.OUTDATED)
        Report.objects.create(guide=self.guide, reporter=self.mod, reason=Report.Reason.SPAM)
        self.assertEqual(self.client.get(self.url()).data["outdated_reports"], 1)

    def test_a_resolved_report_no_longer_counts(self):
        from django.utils import timezone

        Report.objects.create(guide=self.guide, reporter=self.reader, reason="outdated", resolved_at=timezone.now())
        self.assertEqual(self.client.get(self.url()).data["outdated_reports"], 0)

    def test_new_report_reasons_are_accepted(self):
        self.as_user(self.reader)
        for reason in ("outdated", "harassment", "privacy"):
            Report.objects.filter(reporter=self.reader).delete()
            response = self.client.post(self.url("report/"), {"reason": reason}, format="json")
            self.assertEqual(response.status_code, 201, reason)


class CommentKindTests(LifecycleBase):
    def test_every_kind_can_be_written(self):
        self.as_user(self.reader)
        for kind in ("comment", "question", "error", "addition"):
            response = self.client.post(self.url("comments/"), {"body": "Text", "kind": kind}, format="json")
            self.assertEqual((response.status_code, response.data["kind"]), (201, kind))

    def test_an_unknown_kind_is_refused(self):
        self.as_user(self.reader)
        self.assertEqual(self.client.post(self.url("comments/"), {"body": "x", "kind": "rant"}, format="json").status_code, 400)


class HiddenCommentTests(LifecycleBase):
    def setUp(self):
        super().setUp()
        self.comment = GuideComment.objects.create(guide=self.guide, author=self.reader, body="Rude words")

    def hide(self, reason="Personal attack"):
        return self.client.post(self.url(f"comments/{self.comment.pk}/hide/"), {"reason": reason}, format="json")

    def comment_as_seen_by(self, user):
        if user:
            self.as_user(user)
        else:
            self.client.credentials()
        return self.client.get(self.url("comments/")).data[0]

    def test_only_moderators_hide(self):
        self.as_user(self.reader)
        self.assertEqual(self.hide().status_code, 403)
        self.as_user(self.mod)
        self.assertEqual(self.hide().status_code, 200)

    def test_a_reason_is_required(self):
        self.as_user(self.mod)
        self.assertEqual(self.hide("").status_code, 400)

    def test_readers_see_the_reason_but_not_the_text(self):
        self.as_user(self.mod)
        self.hide()
        for viewer in (None, self.reader, self.author):
            data = self.comment_as_seen_by(viewer)
            self.assertTrue(data["hidden"])
            self.assertEqual((data["body"], data["body_html"]), ("", ""))
            self.assertEqual(data["hidden_reason"], "Personal attack")
            self.assertFalse(data["can_edit"])
            self.assertIsNone(data["hidden_by"])

    def test_moderators_still_see_the_text_and_who_hid_it(self):
        self.as_user(self.mod)
        self.hide()
        data = self.comment_as_seen_by(self.mod)
        self.assertEqual((data["body"], data["hidden_by"]), ("Rude words", "mod"))

    def test_the_author_cannot_edit_a_hidden_comment(self):
        self.as_user(self.mod)
        self.hide()
        self.as_user(self.reader)
        response = self.client.put(self.url(f"comments/{self.comment.pk}/"), {"body": "Nice words"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_a_moderator_shows_it_again(self):
        self.as_user(self.mod)
        self.hide()
        self.client.delete(self.url(f"comments/{self.comment.pk}/hide/"))
        data = self.comment_as_seen_by(None)
        self.assertEqual((data["hidden"], data["body"]), (False, "Rude words"))

    def test_hiding_is_recorded_in_the_history(self):
        self.as_user(self.mod)
        self.hide()
        self.assertEqual(self.comment.history.first().history_change_reason, "Comment hidden")


class RelatedAndSuggestTests(LifecycleBase):
    def make(self, title, **extra):
        return Guide.objects.create(title=title, category=self.category, **extra)

    def test_related_guides_share_the_category_and_leave_out_the_guide_itself(self):
        other = self.make("Install Node")
        elsewhere = Guide.objects.create(title="Bake bread", category=Category.objects.create(name="Food"))
        slugs = [g["slug"] for g in self.client.get(self.url("related/")).data]
        self.assertEqual(slugs, [other.slug])
        self.assertNotIn(elsewhere.slug, slugs)

    def test_related_guides_skip_archived_ones_and_stop_at_three(self):
        for n in range(5):
            self.make(f"Guide {n}")
        self.make("Old guide", status=GuideStatus.ARCHIVED)
        data = self.client.get(self.url("related/")).data
        self.assertEqual(len(data), 3)
        self.assertNotIn("Old guide", [g["title"] for g in data])

    def test_a_guide_without_category_has_no_related_guides(self):
        loose = Guide.objects.create(title="Loose")
        self.assertEqual(self.client.get(f"/api/guides/{loose.slug}/related/").data, [])

    def test_suggestions_name_guides_and_categories(self):
        data = self.client.get("/api/guides/suggest/?q=pyth").data
        self.assertEqual([g["title"] for g in data["guides"]], ["Install Python"])
        self.assertEqual(self.client.get("/api/guides/suggest/?q=comp").data["categories"][0]["name"], "Computers")

    def test_suggestions_skip_archived_guides(self):
        self.make("Python archive", status=GuideStatus.ARCHIVED)
        titles = [g["title"] for g in self.client.get("/api/guides/suggest/?q=python").data["guides"]]
        self.assertEqual(titles, ["Install Python"])

    def test_a_typo_gets_the_closest_title(self):
        data = self.client.get("/api/guides/suggest/?q=instal pythn").data
        self.assertEqual((data["guides"], data["did_you_mean"]), ([], "Install Python"))

    def test_one_letter_asks_for_nothing(self):
        self.assertEqual(self.client.get("/api/guides/suggest/?q=p").data["guides"], [])
