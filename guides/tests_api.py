import io
import tempfile
from pathlib import Path
from zipfile import ZipFile

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Category, Guide, GuideComment, Step


class ApiTests(APITestCase):
    def setUp(self):
        cache.clear()  # reset the throttling counters
        self.user = User.objects.create_user("mel", password="geheim-12345")
        self.category = Category.objects.create(name="Technik")
        self.guide = Guide.objects.create(
            title="Python einrichten", category=self.category, summary="Kurz erklärt"
        )
        self.step1 = Step.objects.create(guide=self.guide, order=1, title="Ordner", body="`mkdir x`")
        self.step2 = Step.objects.create(guide=self.guide, order=2, title="Venv", body="Text")

    def login(self):
        response = self.client.post(
            "/api/auth/login/", {"username": "mel", "password": "geheim-12345"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    # Reading
    def test_list_is_public_paginated_and_searchable(self):
        response = self.client.get("/api/guides/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], "python-einrichten")
        self.assertEqual(response.data["results"][0]["category"]["slug"], "technik")
        self.assertEqual(self.client.get("/api/guides/", {"q": "mkdir"}).data["count"], 1)
        self.assertEqual(self.client.get("/api/guides/", {"q": "gibtsnicht"}).data["count"], 0)

    def test_category_filter_and_category_list(self):
        Guide.objects.create(title="Ohne Kategorie")
        self.assertEqual(self.client.get("/api/guides/").data["count"], 2)
        filtered = self.client.get("/api/guides/", {"category": "technik"})
        self.assertEqual(filtered.data["count"], 1)
        categories = self.client.get("/api/categories/")
        self.assertIn("technik", [c["slug"] for c in categories.data])

    def test_detail_contains_steps_and_sanitized_html(self):
        Step.objects.create(
            guide=self.guide, order=3, title="Böse", body="Hi <script>alert(1)</script>"
        )
        data = self.client.get("/api/guides/python-einrichten/").data
        self.assertEqual([s["order"] for s in data["steps"]], [1, 2, 3])
        self.assertIn("<code>mkdir x</code>", data["steps"][0]["body_html"])
        self.assertNotIn("<script", data["steps"][2]["body_html"])

    def test_pdf_endpoint(self):
        response = self.client.get("/api/guides/python-einrichten/pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_guide_attachment_upload_download_replace_and_remove(self):
        png_content = b"\x89PNG\r\n\x1a\nimage-data"
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.login()
            uploaded = self.client.post(
                "/api/guides/python-einrichten/attachment/",
                {"file": SimpleUploadedFile("diagram.png", png_content, content_type="image/png")},
                format="multipart",
            )
            self.assertEqual(uploaded.status_code, 200, uploaded.data)
            self.assertEqual(uploaded.data["attachment_info"]["name"], "diagram.png")
            self.assertEqual(uploaded.data["attachment_info"]["size"], len(png_content))
            self.guide.refresh_from_db()
            first_path = Path(media_root, self.guide.attachment.name)
            self.assertTrue(first_path.is_file())
            self.assertEqual(self.guide.history.first().history_change_reason, "Guide attachment uploaded")
            self.assertEqual(self.guide.history.first().history_user, self.user)
            history = self.client.get("/api/guides/python-einrichten/history/").data
            self.assertEqual(history["guide"][0]["reason"], "Guide attachment uploaded")
            self.assertEqual(history["guide"][0]["attachment"], "diagram.png")
            self.assertEqual(history["guide"][0]["user"], "mel")

            self.client.credentials()
            downloaded = self.client.get("/api/guides/python-einrichten/attachment/")
            self.assertEqual(downloaded.status_code, 200)
            self.assertEqual(downloaded["Content-Type"], "application/octet-stream")
            self.assertIn("attachment;", downloaded["Content-Disposition"])
            self.assertEqual(b"".join(downloaded.streaming_content), png_content)

            self.login()
            office_file = io.BytesIO()
            with ZipFile(office_file, "w") as archive:
                archive.writestr("[Content_Types].xml", "<Types/>")
                archive.writestr("word/document.xml", "<document/>")
            with self.captureOnCommitCallbacks(execute=True):
                replaced = self.client.post(
                    "/api/guides/python-einrichten/attachment/",
                    {"file": SimpleUploadedFile("notes.docx", office_file.getvalue())},
                    format="multipart",
                )
            self.assertEqual(replaced.status_code, 200, replaced.data)
            self.assertEqual(replaced.data["attachment_info"]["name"], "notes.docx")
            self.assertFalse(first_path.exists())

            removed = self.client.delete("/api/guides/python-einrichten/attachment/")
            self.assertEqual(removed.status_code, 204)
            self.assertIsNone(self.client.get("/api/guides/python-einrichten/").data["attachment_info"])
            self.assertEqual(
                self.client.get("/api/guides/python-einrichten/attachment/").status_code,
                404,
            )

    def test_markdown_attachment_can_be_uploaded_and_downloaded(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.login()
            uploaded = self.client.post(
                "/api/guides/python-einrichten/attachment/",
                {
                    "file": SimpleUploadedFile(
                        "reference.md",
                        b"# Reference\n\nMarkdown **works**.\n",
                        content_type="text/markdown",
                    )
                },
                format="multipart",
            )
            self.assertEqual(uploaded.status_code, 200, uploaded.data)
            self.assertEqual(uploaded.data["attachment_info"]["name"], "reference.md")

            self.client.credentials()
            response = self.client.get("/api/guides/python-einrichten/attachment/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                b"".join(response.streaming_content),
                b"# Reference\n\nMarkdown **works**.\n",
            )

    def test_file_only_guide_with_pdf(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.login()
            created = self.client.post(
                "/api/guides/",
                {"title": "Nur als PDF", "summary": "Siehe Datei", "category_id": self.category.pk, "steps": []},
                format="json",
            )
            self.assertEqual(created.status_code, 201, created.data)
            url = f"/api/guides/{created.data['slug']}/attachment/"
            fake_pdf = self.client.post(
                url, {"file": SimpleUploadedFile("anleitung.pdf", b"kein pdf")}, format="multipart"
            )
            self.assertEqual(fake_pdf.status_code, 400)
            uploaded = self.client.post(
                url,
                {"file": SimpleUploadedFile("anleitung.pdf", b"%PDF-1.7 test", content_type="application/pdf")},
                format="multipart",
            )
            self.assertEqual(uploaded.status_code, 200, uploaded.data)
            self.assertEqual(uploaded.data["attachment_info"]["name"], "anleitung.pdf")
            self.assertEqual(uploaded.data["steps"], [])

    def test_new_guide_creation_and_attachment_are_both_in_history(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.login()
            created = self.client.post(
                "/api/guides/",
                {
                    "title": "Guide with attachment",
                    "summary": "A new guide",
                    "steps": [{"title": "Step", "body": "Content"}],
                },
                format="json",
            )
            self.assertEqual(created.status_code, 201, created.data)
            slug = created.data["slug"]
            self.client.post(
                f"/api/guides/{slug}/attachment/",
                {"file": SimpleUploadedFile("reference.txt", b"reference")},
                format="multipart",
            )

            history = self.client.get(f"/api/guides/{slug}/history/").data
            self.assertEqual(history["guide"][0]["reason"], "Guide attachment uploaded")
            self.assertEqual(history["guide"][0]["attachment"], "reference.txt")
            self.assertEqual(history["guide"][0]["user"], "mel")
            self.assertEqual(history["guide"][-1]["type"], "created")
            self.assertEqual(history["guide"][-1]["user"], "mel")

    def test_attachment_upload_requires_permission_and_valid_file(self):
        url = "/api/guides/python-einrichten/attachment/"
        self.assertEqual(
            self.client.post(
                url,
                {"file": SimpleUploadedFile("diagram.png", b"\x89PNG\r\n\x1a\n")},
                format="multipart",
            ).status_code,
            401,
        )
        self.login()
        invalid_type = self.client.post(
            url,
            {"file": SimpleUploadedFile("program.exe", b"not allowed")},
            format="multipart",
        )
        self.assertEqual(invalid_type.status_code, 400)
        self.assertIn("Allowed formats", str(invalid_type.data))

        invalid_image = self.client.post(
            url,
            {"file": SimpleUploadedFile("fake.png", b"not a PNG")},
            format="multipart",
        )
        self.assertEqual(invalid_image.status_code, 400)

        too_large = self.client.post(
            url,
            {"file": SimpleUploadedFile("large.txt", b"x" * (10 * 1024 * 1024 + 1))},
            format="multipart",
        )
        self.assertEqual(too_large.status_code, 400)
        self.guide.is_locked = True
        self.guide.save()
        locked_upload = self.client.post(
            url,
            {"file": SimpleUploadedFile("notes.txt", b"hello")},
            format="multipart",
        )
        self.assertEqual(locked_upload.status_code, 403)

    def test_create_preview_is_sanitized_and_does_not_publish(self):
        self.login()
        payload = {
            "title": "Vorschau-Guide",
            "summary": "Nur eine Vorschau",
            "category_id": self.category.pk,
            "steps": [{"title": "Schritt", "body": "**Fett** <script>alert(1)</script>"}],
        }
        response = self.client.post("/api/guides/preview/", payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("<strong>Fett</strong>", response.data["steps"][0]["body_html"])
        self.assertNotIn("<script", response.data["steps"][0]["body_html"])
        self.assertEqual(Guide.objects.count(), 1)

    def test_update_preview_does_not_publish(self):
        self.login()
        payload = {
            "title": "Geänderter Titel",
            "summary": self.guide.summary,
            "category_id": self.category.pk,
            "steps": [{"id": self.step1.pk, "title": "Ordner", "body": "Vorschau"}],
        }
        response = self.client.post(
            "/api/guides/python-einrichten/preview/", payload, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.guide.refresh_from_db()
        self.assertEqual(self.guide.title, "Python einrichten")

    def test_update_preview_rejects_foreign_step_id(self):
        other = Guide.objects.create(title="Anderer")
        foreign = Step.objects.create(guide=other, order=1, title="Fremd", body="x")
        self.login()
        payload = {"title": "X", "steps": [{"id": foreign.id, "title": "Fremd", "body": "x"}]}
        response = self.client.post(
            "/api/guides/python-einrichten/preview/", payload, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("steps", response.data)

    def test_preview_requires_write_access(self):
        response = self.client.post(
            "/api/guides/preview/",
            {"title": "Vorschau", "steps": []},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_comments_are_public_to_read_and_require_login_to_create(self):
        self.assertEqual(
            self.client.post(
                "/api/guides/python-einrichten/comments/",
                {"body": "Anonym"},
                format="json",
            ).status_code,
            401,
        )
        self.login()
        created = self.client.post(
            "/api/guides/python-einrichten/comments/",
            {"body": "Hilfreicher Artikel!"},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["author"], "mel")
        self.assertTrue(created.data["can_edit"])
        self.assertEqual(GuideComment.objects.get().guide, self.guide)

        preview = self.client.post(
            "/api/guides/python-einrichten/comments/preview/",
            {"body": "**Bold** <script>alert(1)</script>"},
            format="json",
        )
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertIn("<strong>Bold</strong>", preview.data["body_html"])
        self.assertNotIn("<script", preview.data["body_html"])
        self.assertEqual(GuideComment.objects.count(), 1)

        comment = GuideComment.objects.get()
        updated = self.client.put(
            f"/api/guides/python-einrichten/comments/{comment.pk}/",
            {"body": "**Updated** comment"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertIn("<strong>Updated</strong>", updated.data["body_html"])
        self.assertIsNotNone(updated.data["edited_at"])
        comment.refresh_from_db()
        self.assertEqual(comment.history.first().history_change_reason, "Comment edited")
        self.assertEqual(comment.history.first().history_user, self.user)

        other_user = User.objects.create_user("other", password="other-password")
        self.client.force_authenticate(user=other_user)
        self.assertEqual(
            self.client.put(
                f"/api/guides/python-einrichten/comments/{comment.pk}/",
                {"body": "Not allowed"},
                format="json",
            ).status_code,
            403,
        )
        self.client.force_authenticate(user=None)
        self.client.credentials()
        listing = self.client.get("/api/guides/python-einrichten/comments/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data[0]["body"], "**Updated** comment")
        self.assertFalse(listing.data[0]["can_edit"])

    def test_edit_comment_with_non_numeric_id_is_404(self):
        self.login()
        response = self.client.put(
            "/api/guides/python-einrichten/comments/abc/", {"body": "x"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    # Writing
    def test_write_requires_token(self):
        self.assertEqual(self.client.post("/api/guides/", {"title": "x"}, format="json").status_code, 401)
        self.assertEqual(
            self.client.put("/api/guides/python-einrichten/", {"title": "x"}, format="json").status_code,
            401,
        )

    def test_patch_not_allowed(self):
        self.login()
        self.assertEqual(self.client.patch("/api/guides/python-einrichten/", {}, format="json").status_code, 405)

    def test_create_with_steps_records_history(self):
        self.login()
        payload = {
            "title": "Neuer Guide",
            "summary": "Test",
            "category_id": self.category.pk,
            "change_comment": "Erste Version",
            "steps": [
                {"title": "Eins", "body": "A"},
                {"title": "Zwei", "body": "B"},
            ],
        }
        response = self.client.post("/api/guides/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        guide = Guide.objects.get(slug=response.data["slug"])
        self.assertEqual(guide.created_by, self.user)
        self.assertEqual([s.order for s in guide.steps.all()], [1, 2])
        record = guide.history.first()
        self.assertEqual(record.history_change_reason, "Erste Version")
        self.assertEqual(record.history_user, self.user)

    def test_update_matches_steps_by_id(self):
        self.login()
        payload = {
            "title": "Python einrichten (neu)",
            "summary": "Kurz erklärt",
            "category_id": self.category.pk,
            "change_comment": "Schritte umgebaut",
            "steps": [
                {"title": "Neuer Anfang", "body": "N"},  # neu, steht jetzt vorn
                {"id": self.step1.id, "title": "Ordner anlegen", "body": "`mkdir x`"},  # changed
                # step2 missing -> gets deleted
            ],
        }
        response = self.client.put("/api/guides/python-einrichten/", payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.guide.refresh_from_db()
        self.assertEqual(self.guide.title, "Python einrichten (neu)")
        self.assertEqual(self.guide.slug, "python-einrichten")  # the URL stays stable
        titles = [s.title for s in self.guide.steps.all()]
        self.assertEqual(titles, ["Neuer Anfang", "Ordner anlegen"])
        self.assertTrue(Step.objects.filter(pk=self.step1.pk).exists())  # gleiche id behalten
        self.assertFalse(Step.objects.filter(pk=self.step2.pk).exists())
        self.assertEqual(self.guide.history.first().history_change_reason, "Schritte umgebaut")

    def test_update_rejects_foreign_step_id(self):
        other = Guide.objects.create(title="Anderer")
        foreign = Step.objects.create(guide=other, order=1, title="Fremd", body="x")
        self.login()
        payload = {"title": "X", "steps": [{"id": foreign.id, "title": "Fremd", "body": "x"}]}
        response = self.client.put("/api/guides/python-einrichten/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Step.objects.filter(pk=foreign.pk, guide=other).exists())

    def test_history_endpoint(self):
        self.login()
        self.client.put(
            "/api/guides/python-einrichten/",
            {"title": "Neu", "change_comment": "Titel geändert"},
            format="json",
        )
        data = self.client.get("/api/guides/python-einrichten/history/").data
        self.assertEqual(data["guide"][0]["reason"], "Titel geändert")
        self.assertEqual(data["guide"][0]["user"], "mel")
        self.assertEqual(data["guide"][0]["type"], "changed")
        self.assertGreaterEqual(len(data["steps"]), 2)

    def test_cors_header_for_nuxt_origin(self):
        response = self.client.get("/api/guides/", HTTP_ORIGIN="http://localhost:3000")
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://localhost:3000")


def make_docx(text):
    """A minimal, valid Word document with one paragraph."""
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        archive.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>",
        )
    return buffer.getvalue()


class AttachmentPreviewTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("mel", password="geheim-12345")
        self.guide = Guide.objects.create(title="Datei-Guide")
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)

    def login(self):
        self.client.force_authenticate(user=self.user)

    def upload(self, name, content):
        self.login()
        response = self.client.post(
            f"/api/guides/{self.guide.slug}/attachment/",
            {"file": SimpleUploadedFile(name, content)},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.client.force_authenticate(user=None)
        return response.data["attachment_info"]

    def test_pdf_can_be_shown_inline(self):
        info = self.upload("anleitung.pdf", b"%PDF-1.7 test")
        self.assertEqual(info["kind"], "pdf")
        self.assertEqual(info["view_url"], f"/api/guides/{self.guide.slug}/attachment/?inline=1")
        response = self.client.get(info["view_url"])
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response["Content-Disposition"].startswith("inline"))
        self.assertEqual(response["X-Frame-Options"], "SAMEORIGIN")
        response.close()
        # Without ?inline=1 it is still a download
        download = self.client.get(info["download_url"])
        self.assertTrue(download["Content-Disposition"].startswith("attachment"))
        download.close()

    def test_text_files_are_never_served_inline(self):
        info = self.upload("notiz.txt", b"<script>alert(1)</script>")
        self.assertEqual(info["kind"], "html")
        self.assertIsNone(info["view_url"])
        self.assertIn("&lt;script&gt;", info["preview_html"])
        response = self.client.get(f"/api/guides/{self.guide.slug}/attachment/?inline=1")
        self.assertEqual(response["Content-Type"], "application/octet-stream")
        self.assertTrue(response["Content-Disposition"].startswith("attachment"))
        response.close()

    def test_docx_and_markdown_get_sanitized_preview(self):
        info = self.upload("brief.docx", make_docx("Hallo aus Word"))
        self.assertIn("Hallo aus Word", info["preview_html"])
        info = self.upload("liste.md", b"# Titel\n\n- **fett**\n\n<script>x</script>")
        self.assertIn("<strong>fett</strong>", info["preview_html"])
        self.assertNotIn("<script", info["preview_html"])

    def test_csv_becomes_table(self):
        info = self.upload("daten.csv", "Name;Wert\nÄpfel;3\n".encode())
        self.assertIn("<th>Name</th>", info["preview_html"])
        self.assertIn("<td>Äpfel</td>", info["preview_html"])

    def test_preview_before_publishing_saves_nothing(self):
        self.login()
        response = self.client.post(
            "/api/guides/attachment-preview/",
            {"file": SimpleUploadedFile("entwurf.md", b"**Entwurf**")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["kind"], "html")
        self.assertIn("<strong>Entwurf</strong>", response.data["preview_html"])
        self.guide.refresh_from_db()
        self.assertFalse(self.guide.attachment)

        pdf = self.client.post(
            "/api/guides/attachment-preview/",
            {"file": SimpleUploadedFile("x.pdf", b"%PDF-1.7")},
            format="multipart",
        )
        self.assertEqual(pdf.data, {"kind": "pdf", "preview_html": ""})

    def test_preview_requires_login(self):
        response = self.client.post(
            "/api/guides/attachment-preview/",
            {"file": SimpleUploadedFile("x.md", b"x")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 401)

    def test_reserved_slug(self):
        self.assertNotEqual(Guide.objects.create(title="Attachment Preview").slug, "attachment-preview")


class MarkdownRenderTests(APITestCase):
    """Live preview rendering: same sanitizer as saved guides, no database writes."""

    url = "/api/markdown/render/"

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("mel", password="geheim-12345")

    def test_renders_and_sanitizes_in_order(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url, {"texts": ["**fett**", "<script>alert(1)</script>Text", ""]}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        first, second, third = response.data["html"]
        self.assertIn("<strong>fett</strong>", first)
        self.assertNotIn("<script", second)
        self.assertEqual(third, "")
        self.assertEqual(Guide.objects.count(), 0)

    def test_requires_login_and_limits_size(self):
        self.assertEqual(self.client.post(self.url, {"texts": ["x"]}, format="json").status_code, 401)
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.post(self.url, {"texts": []}, format="json").status_code, 400)
        self.assertEqual(self.client.post(self.url, {"texts": ["x"] * 101}, format="json").status_code, 400)
        self.assertEqual(self.client.post(self.url, {"texts": ["x" * 5001]}, format="json").status_code, 400)
        too_much = ["y" * 5000] * 21
        self.assertEqual(self.client.post(self.url, {"texts": too_much}, format="json").status_code, 400)
