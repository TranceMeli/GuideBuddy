"""Deleting guides: only the author and moderators, with the usual write rules."""

import tempfile
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Guide, GuideElement, GuideImage, Profile, Step
from .permissions import MODERATOR_GROUP
from .tests_types import png_bytes


class DeleteGuideTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user("autorin", password="geheim-12345")
        self.other = User.objects.create_user("eva", password="geheim-12345")
        self.mod = User.objects.create_user("mod", password="geheim-12345")
        self.mod.groups.add(Group.objects.get(name=MODERATOR_GROUP))
        self.guide = Guide.objects.create(title="Zum Löschen", guide_type="page", created_by=self.author)
        GuideElement.objects.create(guide=self.guide, kind="step", text="S")
        Step.objects.create(guide=self.guide, title="S", body="b")
        self.url = f"/api/guides/{self.guide.slug}/"

    def delete(self, user):
        self.client.force_authenticate(user=user)
        return self.client.delete(self.url)

    def test_author_can_delete_and_history_stays(self):
        self.assertEqual(self.delete(self.author).status_code, 204)
        self.assertFalse(Guide.objects.filter(pk=self.guide.pk).exists())
        self.assertFalse(Step.objects.filter(guide_id=self.guide.pk).exists())
        deleted = Guide.history.filter(id=self.guide.pk).first()
        self.assertEqual(deleted.history_type, "-")
        self.assertEqual(deleted.history_user, self.author)
        self.assertEqual(deleted.history_change_reason, "Guide deleted")

    def test_others_cannot_delete(self):
        response = self.delete(self.other)
        self.assertEqual(response.status_code, 403)
        self.assertIn("author", str(response.data))
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.delete(self.url).status_code, 401)
        self.assertTrue(Guide.objects.filter(pk=self.guide.pk).exists())

    def test_guides_without_author_only_by_moderators(self):
        self.guide.created_by = None
        self.guide.save()
        self.assertEqual(self.delete(self.other).status_code, 403)
        self.assertEqual(self.delete(self.mod).status_code, 204)

    def test_locked_guide_only_by_moderators(self):
        self.guide.is_locked = True
        self.guide.save()
        self.assertEqual(self.delete(self.author).status_code, 403)
        self.assertEqual(self.delete(self.mod).status_code, 204)

    def test_banned_author_cannot_delete(self):
        Profile.objects.create(user=self.author, banned_at="2026-01-01T00:00:00Z")
        self.assertEqual(self.delete(self.author).status_code, 403)

    def test_files_are_removed(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as media, override_settings(MEDIA_ROOT=media):
            self.guide.attachment.save("anleitung.pdf", ContentFile(b"%PDF-1.7 x"))
            image = GuideImage(guide=self.guide, alt="Bild", uploaded_by=self.author)
            image.file.save("bild.png", ContentFile(png_bytes()))
            paths = [Path(media) / self.guide.attachment.name, Path(media) / image.file.name]
            self.assertTrue(all(path.exists() for path in paths))
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self.delete(self.author).status_code, 204)
            self.assertFalse(any(path.exists() for path in paths))
            self.assertFalse(GuideImage.objects.filter(pk=image.pk).exists())
