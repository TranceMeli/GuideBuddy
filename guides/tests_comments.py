"""Comments: on a guide or an element, replies, questions with answers, "helpful", reports."""

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import Guide, GuideComment, GuideElement, Report
from .permissions import MODERATOR_GROUP


class CommentThreadTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user("author", password="geheim-12345")
        self.anna = User.objects.create_user("anna", password="geheim-12345")
        self.ben = User.objects.create_user("ben", password="geheim-12345")
        self.mod = User.objects.create_user("mod", password="geheim-12345")
        self.mod.groups.add(Group.objects.get(name=MODERATOR_GROUP))
        self.guide = Guide.objects.create(title="Install", guide_type="page", created_by=self.author)
        self.section = GuideElement.objects.create(guide=self.guide, order=1, kind="section", text="Install")
        self.step = GuideElement.objects.create(guide=self.guide, order=2, kind="step", text="Start the installer")
        self.box = GuideElement.objects.create(guide=self.guide, order=3, kind="important", text="Tick the box")
        self.other_guide = Guide.objects.create(title="Other", guide_type="page")
        self.foreign = GuideElement.objects.create(guide=self.other_guide, order=1, kind="step", text="x")
        self.url = f"/api/guides/{self.guide.slug}/comments/"

    def post(self, user, **data):
        self.client.force_authenticate(user=user)
        return self.client.post(self.url, {"body": "Hello", **data}, format="json")

    def test_comment_on_an_element_keeps_its_name(self):
        response = self.post(self.anna, element_id=self.step.pk, kind="question")
        self.assertEqual(response.status_code, 201, response.data)
        data = response.data
        self.assertEqual((data["kind"], data["element"]), ("question", self.step.pk))
        self.assertEqual(data["anchor"], "Step 1: Start the installer")
        self.step.delete()  # the comment stays and still says what it was about
        listed = self.client.get(self.url).data
        self.assertEqual((listed[0]["element"], listed[0]["anchor"]), (None, "Step 1: Start the installer"))

    def test_plain_comment_and_foreign_element(self):
        data = self.post(self.anna).data
        self.assertEqual((data["kind"], data["element"], data["parent"], data["anchor"]), ("comment", None, None, ""))
        self.assertEqual(self.post(self.anna, element_id=self.foreign.pk).status_code, 404)

    def test_replies_inherit_the_place_and_stay_one_level_deep(self):
        top = self.post(self.anna, element_id=self.box.pk, kind="question").data
        reply = self.post(self.ben, parent_id=top["id"], kind="question")
        self.assertEqual(reply.status_code, 201, reply.data)
        self.assertEqual((reply.data["kind"], reply.data["element"], reply.data["anchor"]), ("comment", self.box.pk, top["anchor"]))
        self.assertEqual(reply.data["parent"], top["id"])
        deeper = self.post(self.anna, parent_id=reply.data["id"])
        self.assertEqual(deeper.status_code, 400)
        elsewhere = self.post(self.anna, parent_id=GuideComment.objects.create(guide=self.other_guide, body="x").pk)
        self.assertEqual(elsewhere.status_code, 404)

    def test_helpful_once_and_never_for_ones_own_comment(self):
        comment = self.post(self.anna).data
        url = f"{self.url}{comment['id']}/helpful/"
        self.client.force_authenticate(user=self.anna)
        self.assertEqual(self.client.post(url).status_code, 400)
        self.client.force_authenticate(user=self.ben)
        first = self.client.post(url).data
        again = self.client.post(url).data
        self.assertEqual((first["helpful_count"], again["helpful_count"], again["helpful"]), (1, 1, True))
        self.client.force_authenticate(user=self.mod)
        self.assertEqual(self.client.post(url).data["helpful_count"], 2)
        self.assertFalse(self.client.get(self.url).data[0]["helpful"] is None)
        self.client.force_authenticate(user=self.ben)
        removed = self.client.delete(url).data
        self.assertEqual((removed["helpful_count"], removed["helpful"]), (1, False))
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(url).status_code, 401)

    def test_answers_can_be_marked_by_the_asker_the_guide_author_and_moderators(self):
        question = self.post(self.anna, kind="question").data
        first = self.post(self.ben, parent_id=question["id"]).data
        second = self.post(self.author, parent_id=question["id"]).data
        url = lambda c: f"{self.url}{c['id']}/answer/"  # noqa: E731

        self.client.force_authenticate(user=self.ben)  # not allowed: neither asker nor author
        self.assertEqual(self.client.post(url(first)).status_code, 403)
        self.client.force_authenticate(user=self.anna)
        marked = self.client.post(url(first)).data
        self.assertTrue(marked["is_answer"])
        self.client.force_authenticate(user=self.author)
        self.assertTrue(self.client.post(url(second)).data["is_answer"])  # one answer per question
        self.assertFalse(GuideComment.objects.get(pk=first["id"]).is_answer)
        self.client.force_authenticate(user=self.mod)
        self.assertFalse(self.client.delete(url(second)).data["is_answer"])
        # only replies to a question can be answers
        top = self.post(self.anna).data
        reply = self.post(self.ben, parent_id=top["id"]).data
        self.client.force_authenticate(user=self.mod)
        self.assertEqual(self.client.post(url(reply)).status_code, 403)
        self.assertEqual(self.client.post(url(question)).status_code, 403)

    def test_list_flags_for_the_viewer(self):
        question = self.post(self.anna, kind="question").data
        self.post(self.author, parent_id=question["id"])
        self.client.force_authenticate(user=self.anna)
        listed = {c["id"]: c for c in self.client.get(self.url).data}
        reply = next(c for c in listed.values() if c["parent"])
        self.assertTrue(reply["by_guide_author"])
        self.assertTrue(reply["can_mark_answer"])
        self.assertTrue(listed[question["id"]]["can_edit"])
        self.assertFalse(listed[question["id"]]["can_mark_answer"])
        self.client.force_authenticate(user=self.ben)
        reply = next(c for c in self.client.get(self.url).data if c["parent"])
        self.assertFalse(reply["can_mark_answer"])

    def test_reporting_a_comment(self):
        comment = self.post(self.anna, body="Buy pills here").data
        url = f"{self.url}{comment['id']}/report/"
        self.client.force_authenticate(user=self.ben)
        first = self.client.post(url, {"reason": "spam"}, format="json")
        self.assertEqual(first.status_code, 201, first.data)
        again = self.client.post(url, {"reason": "spam"}, format="json")
        self.assertIn("already", again.data["detail"])
        report = Report.objects.get()
        self.assertEqual((report.reported_comment_id, report.guide_id), (comment["id"], self.guide.pk))
        self.client.force_authenticate(user=self.mod)
        listed = self.client.get("/api/reports/").data
        rows = listed["results"] if isinstance(listed, dict) else listed
        self.assertEqual(rows[0]["reported_comment_body"], "Buy pills here")
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(url, {"reason": "spam"}, format="json").status_code, 401)
