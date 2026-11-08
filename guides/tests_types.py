"""Tests for the guide types and their content blocks (docs/guide-types.md)."""

import io
import tempfile

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APITestCase

from .models import Category, Guide, GuideElement, GuideImage


def png_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), "blue").save(buffer, "PNG")
    return buffer.getvalue()


def page_payload(**extra):
    payload = {
        "guide_type": "page",
        "title": "Change a bike inner tube",
        "subtitle": "In ten minutes",
        "elements": [
            {"kind": "section", "text": "Take the wheel off"},
            {"kind": "step", "text": "Release the brake"},
            {"kind": "text", "text": "Open the **brake** lever."},
            {"kind": "important", "text": "Release the brake <script>alert(1)</script> **first**."},
            {"kind": "result", "text": "The wheel is free."},
            {"kind": "terminal", "text": "$ echo hi\nhi"},
        ],
    }
    payload.update(extra)
    return payload


class TypedGuideTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("mel", password="geheim-12345")
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="Bikes")

    def create(self, payload, status=201):
        response = self.client.post("/api/guides/", payload, format="json")
        self.assertEqual(response.status_code, status, response.data)
        return response

    def test_page_guide_round_trip(self):
        data = self.create(page_payload(category_id=self.category.pk)).data
        self.assertEqual(data["guide_type"], "page")
        self.assertEqual([e["kind"] for e in data["elements"]], ["section", "step", "text", "important", "result", "terminal"])
        self.assertIn("<strong>brake</strong>", data["elements"][2]["html"])
        self.assertNotIn("<script", data["elements"][3]["html"])
        self.assertIn("<strong>first</strong>", data["elements"][3]["html"])
        self.assertIn("codehilite", data["elements"][5]["html"])
        listing = self.client.get("/api/guides/", {"type": "page"}).data["results"]
        self.assertEqual(listing[0]["step_count"], 1)

    def test_warning_and_danger_notices(self):
        payload = {"guide_type": "page", "title": "Hot pot", "elements": [
            {"kind": "warning", "text": "The pot is **hot**. <script>x</script>"},
            {"kind": "danger", "text": "Mains voltage can be fatal."},
        ]}
        data = self.create(payload).data
        self.assertEqual([e["kind"] for e in data["elements"]], ["warning", "danger"])
        self.assertIn("<strong>hot</strong>", data["elements"][0]["html"])
        self.assertNotIn("<script", data["elements"][0]["html"])
        too_long = {**payload, "elements": [{"kind": "danger", "text": "x" * 1001}]}
        self.create(too_long, status=400)

    def test_an_empty_guide_is_fine(self):
        data = self.create({"guide_type": "page", "title": "Blank"}).data
        self.assertEqual(data["elements"], [])

    def test_type_rules(self):
        response = self.create({"guide_type": "page", "title": "X", "steps": [{"title": "a", "body": "b"}]}, status=400)
        self.assertIn("steps", response.data)
        response = self.create({"title": "Free", "elements": [{"kind": "text", "text": "x"}]}, status=400)
        self.assertIn("elements", response.data)
        old = self.create({"title": "Old", "steps": [{"title": "a", "body": "b"}]}).data
        self.assertEqual(old["guide_type"], "free")
        self.assertEqual(old["elements"], [])

    def test_unknown_kind_and_limits(self):
        self.create(page_payload(elements=[{"kind": "hologram", "text": "x"}]), status=400)
        too_long = page_payload(elements=[{"kind": "step", "text": "x" * 161}])
        self.assertIn("elements", self.create(too_long, status=400).data)
        too_many = page_payload(elements=[{"kind": "divider"} for _ in range(301)])
        self.assertIn("elements", self.create(too_many, status=400).data)

    def test_kind_data_is_cleaned_and_checked(self):
        elements = [
            {"kind": "link", "text": "The docs", "data": {"url": "https://docs.python.org", "evil": 1}},
            {"kind": "table", "data": {"rows": [["Name", "Use"], ["pip"]]}},
            {"kind": "diagram", "data": {"nodes": ["A", " ", "B"]}},
            {"kind": "compare", "text": "Quotes", "data": {"wrong": "print 'x'", "right": "print('x')", "language": "python"}},
            {"kind": "collapsible", "text": "Why?", "data": {"body": "Because **it works**."}},
            {"kind": "checklist", "text": "One\nTwo"},
            {"kind": "list", "text": "One\nTwo"},
            {"kind": "quote", "text": "Be kind.", "data": {"source": "Anon"}},
        ]
        data = self.create(page_payload(elements=elements)).data["elements"]
        self.assertEqual(data[0]["data"], {"url": "https://docs.python.org"})
        self.assertEqual(data[1]["data"]["rows"], [["Name", "Use"], ["pip", ""]])
        self.assertEqual(data[2]["data"]["nodes"], ["A", "B"])
        self.assertIn("codehilite", data[3]["data"]["wrong_html"])
        self.assertIn("<strong>it works</strong>", data[4]["html"])
        self.assertEqual(data[6]["html"].count("<li>"), 2)
        self.assertEqual(data[7]["data"], {"source": "Anon"})
        bad_url = page_payload(elements=[{"kind": "link", "text": "x", "data": {"url": "javascript:alert(1)"}}])
        self.assertIn("elements", self.create(bad_url, status=400).data)
        wide = page_payload(elements=[{"kind": "table", "data": {"rows": [["a"] * 9]}}])
        self.assertIn("elements", self.create(wide, status=400).data)

    def test_update_keeps_ids_reorders_and_deletes_the_rest(self):
        data = self.create(page_payload()).data
        slug = data["slug"]
        first, second, third = data["elements"][:3]
        payload = {"title": "T", "elements": [third | {"text": "Moved first"}, first, {"kind": "divider"}]}
        response = self.client.put(f"/api/guides/{slug}/", payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        elements = response.data["elements"]
        self.assertEqual([e["id"] for e in elements[:2]], [third["id"], first["id"]])
        self.assertEqual(elements[0]["text"], "Moved first")
        self.assertEqual(elements[2]["kind"], "divider")
        guide = Guide.objects.get(slug=slug)
        self.assertEqual(guide.elements.count(), 3)
        self.assertFalse(GuideElement.objects.filter(pk=second["id"]).exists())
        self.assertEqual(list(guide.elements.values_list("order", flat=True)), [1, 2, 3])

    def test_foreign_ids_are_rejected(self):
        other = self.create(page_payload(title="Other")).data
        mine = self.create(page_payload()).data
        payload = {"title": "T", "elements": [{"id": other["elements"][0]["id"], "kind": "section", "text": "t"}]}
        response = self.client.put(f"/api/guides/{mine['slug']}/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("elements", response.data)

    def test_type_cannot_change(self):
        slug = self.create(page_payload()).data["slug"]
        response = self.client.put(f"/api/guides/{slug}/", {"title": "T", "guide_type": "free"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("guide_type", response.data)

    def test_search_finds_text_inside_elements(self):
        self.create(page_payload())
        self.create({"guide_type": "page", "title": "Other", "elements": [{"kind": "text", "text": "Nothing here"}]})
        titles = [g["title"] for g in self.client.get("/api/guides/", {"q": "brake"}).data["results"]]
        self.assertEqual(titles, ["Change a bike inner tube"])

    def test_preview_of_a_new_guide_saves_nothing(self):
        before = (Guide.objects.count(), GuideElement.objects.count())
        response = self.client.post("/api/guides/preview/", page_payload(), format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("<strong>first</strong>", response.data["elements"][3]["html"])
        self.assertEqual((Guide.objects.count(), GuideElement.objects.count()), before)
        self.assertEqual(Guide.history.count(), 0)

    def test_preview_of_an_existing_guide_keeps_it_unchanged(self):
        slug = self.create(page_payload()).data["slug"]
        payload = {"title": "Preview title", "elements": [{"kind": "text", "text": "Only"}]}
        response = self.client.post(f"/api/guides/{slug}/preview/", payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["title"], "Preview title")
        guide = Guide.objects.get(slug=slug)
        self.assertEqual(guide.title, "Change a bike inner tube")
        self.assertEqual(guide.elements.count(), 6)

    def test_image_element(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as media, override_settings(MEDIA_ROOT=media):
            image = self.client.post(
                "/api/images/", {"file": SimpleUploadedFile("b.png", png_bytes()), "alt": "Installer", "kind": "mockup"}, format="multipart"
            ).data
            elements = [{"kind": "image", "text": "", "image_id": image["id"], "data": {"markers": [{"x": 1, "y": 2, "text": "dropped"}]}}]
            data = self.create(page_payload(elements=elements)).data["elements"][0]
            self.assertEqual(data["image"]["kind"], "mockup")
            self.assertEqual(data["data"], {})
            # an image id on another kind of element is ignored
            wrong = [{"kind": "text", "text": "x", "image_id": image["id"]}]
            self.assertIsNone(self.create(page_payload(elements=wrong)).data["elements"][0]["image"])

    def test_list_filters(self):
        self.create(page_payload(difficulty="beginner", duration_minutes=15))
        self.create({"title": "Long", "difficulty": "advanced", "duration_minutes": 90})
        guides = lambda **params: [g["title"] for g in self.client.get("/api/guides/", params).data["results"]]  # noqa: E731
        self.assertEqual(guides(difficulty="beginner"), ["Change a bike inner tube"])
        self.assertEqual(guides(max_duration="30"), ["Change a bike inner tube"])
        self.assertEqual(guides(type="free"), ["Long"])
        self.assertEqual(guides(has_pdf="1"), [])


class GuideImageTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.media = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.user = User.objects.create_user("mel", password="geheim-12345")
        self.other = User.objects.create_user("eva", password="geheim-12345")

    def upload(self, user, content=None, name="bild.png", alt="Ein Rad", status=201):
        self.client.force_authenticate(user=user)
        response = self.client.post(
            "/api/images/", {"file": SimpleUploadedFile(name, content or png_bytes()), "alt": alt}, format="multipart"
        )
        self.assertEqual(response.status_code, status, response.data)
        return response.data

    def get(self, url, user=None):
        self.client.force_authenticate(user=user)
        response = self.client.get(url)
        if hasattr(response, "streaming_content"):
            response.close()
        return response

    def test_upload_validation(self):
        self.upload(self.user, content=b"<svg xmlns='http://www.w3.org/2000/svg'/>", name="x.svg", status=400)
        self.upload(self.user, content=b"not an image", name="x.png", status=400)
        self.upload(self.user, alt="", status=400)
        self.client.force_authenticate(user=None)
        response = self.client.post("/api/images/", {"file": SimpleUploadedFile("b.png", png_bytes()), "alt": "x"}, format="multipart")
        self.assertEqual(response.status_code, 401)

    def test_image_is_private_until_a_guide_uses_it(self):
        image = self.upload(self.user)
        self.assertEqual((image["width"], image["height"]), (4, 3))
        self.assertEqual(self.get(image["url"], self.user).status_code, 200)
        self.assertEqual(self.get(image["url"], self.other).status_code, 404)
        self.assertEqual(self.get(image["url"]).status_code, 404)

        # Somebody else cannot attach my unused image to their guide
        self.client.force_authenticate(user=self.other)
        stolen = page_payload(elements=[{"kind": "image", "image_id": image["id"]}])
        self.assertEqual(self.client.post("/api/guides/", stolen, format="json").status_code, 400)

        self.client.force_authenticate(user=self.user)
        payload = page_payload(elements=[{"kind": "image", "image_id": image["id"]}])
        data = self.client.post("/api/guides/", payload, format="json").data
        self.assertEqual(data["elements"][0]["image"]["alt"], "Ein Rad")
        self.assertEqual(GuideImage.objects.get(pk=image["id"]).guide.slug, data["slug"])

        response = self.client.get(image["url"])
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn("sandbox", response["Content-Security-Policy"])
        response.close()
        self.assertEqual(self.get(image["url"]).status_code, 200)  # public now


class GuideLanguageTests(APITestCase):
    """Every guide carries the language of its content (BCP 47 tag); English only for now."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("mel", password="geheim-12345")
        self.client.force_authenticate(user=self.user)

    def test_default_filter_and_validation(self):
        default = self.client.post("/api/guides/", {"title": "Change a tube"}, format="json").data
        self.assertEqual(default["language"], "en")
        listing = self.client.get("/api/guides/", {"language": "en"}).data["results"]
        self.assertEqual([g["slug"] for g in listing], [default["slug"]])
        for other in ("de", "klingon"):
            bad = self.client.post("/api/guides/", {"title": "X", "language": other}, format="json")
            self.assertEqual(bad.status_code, 400)
            self.assertIn("language", bad.data)

    def test_pdf_carries_the_guide_language(self):
        from django.template.loader import render_to_string

        guide = Guide.objects.create(title="Tube", language="en")
        for name in ("guides/guide_pdf.html", "guides/guide_pdf_simple.html"):
            html = render_to_string(name, {"guide": guide, "steps": [], "frontend_url": "https://x.example"})
            self.assertIn('<html lang="en">', html)


class TextStyleTests(TestCase):
    """Text styles (colour, highlight, font) are class names that survive rendering and PDF."""

    def test_pdf_keeps_text_styles_and_has_their_rules(self):
        from types import SimpleNamespace

        from django.template.loader import render_to_string

        guide = Guide.objects.create(title="Styles")
        steps = [SimpleNamespace(title="One", body='A <span class="c-teal">teal</span> and <span class="h-yellow">marked</span> word')]
        for name in ("guides/guide_pdf.html", "guides/guide_pdf_simple.html"):
            html = render_to_string(name, {"guide": guide, "steps": steps, "frontend_url": "https://x.example"})
            self.assertIn('<span class="c-teal">teal</span>', html)
            self.assertIn('<span class="h-yellow">marked</span>', html)
            self.assertIn(".h-yellow {", html)
            self.assertIn("Updated: ", html)

    def test_frontend_and_backend_lists_match(self):
        """utils/textStyles.ts and TEXT_STYLE_CLASSES name the same styles."""
        import re
        from pathlib import Path

        from guides.templatetags.guide_extras import TEXT_STYLE_CLASSES

        source = (Path(__file__).resolve().parent.parent / "frontend" / "app" / "utils" / "textStyles.ts").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r"value: '([chf]-[a-z]+)'", source)), TEXT_STYLE_CLASSES)


class ImageCaptionTests(APITestCase):
    """An image can carry a caption and a kind, so a mockup is never shown as a screenshot."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("mel", password="geheim-12345")
        self.client.force_authenticate(user=self.user)

    def upload(self, **extra):
        data = {"file": SimpleUploadedFile("b.png", png_bytes()), "alt": "Editor window", **extra}
        return self.client.post("/api/images/", data, format="multipart")

    def test_caption_and_kind_are_stored_and_returned(self):
        response = self.upload(caption="  The editor with the output panel ", kind="mockup")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["caption"], "The editor with the output panel")
        self.assertEqual(response.data["kind"], "mockup")

    def test_both_are_optional(self):
        response = self.upload()
        self.assertEqual(response.status_code, 201)
        self.assertEqual((response.data["caption"], response.data["kind"]), ("", ""))

    def test_unknown_kind_is_rejected(self):
        response = self.upload(kind="hologram")
        self.assertEqual(response.status_code, 400)
        self.assertIn("kind", response.data)

    def test_element_image_carries_caption_and_kind(self):
        image = self.upload(caption="Result in the browser", kind="screenshot").data
        guide = self.client.post(
            "/api/guides/",
            {
                "title": "With image", "guide_type": "page",
                "elements": [{"kind": "image", "image_id": image["id"]}],
            },
            format="json",
        )
        self.assertEqual(guide.status_code, 201)
        shown = guide.data["elements"][0]["image"]
        self.assertEqual((shown["caption"], shown["kind"]), ("Result in the browser", "screenshot"))


class TemplateFieldTests(APITestCase):
    """Fields the reading templates need: cover images."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("mel", password="geheim-12345")
        self.client.force_authenticate(user=self.user)

    def test_cover_image(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as media, override_settings(MEDIA_ROOT=media):
            image = self.client.post(
                "/api/images/", {"file": SimpleUploadedFile("b.png", png_bytes()), "alt": "Rad"}, format="multipart"
            ).data
            data = self.client.post("/api/guides/", {"title": "Mit Bild", "cover_image_id": image["id"]}, format="json").data
            self.assertEqual(data["cover_image"]["alt"], "Rad")
            listing = self.client.get("/api/guides/").data["results"]
            self.assertEqual(listing[0]["cover_image"]["id"], image["id"])
            other = User.objects.create_user("eva", password="geheim-12345")
            self.client.force_authenticate(user=other)
            stolen = self.client.post("/api/guides/", {"title": "Fremd", "cover_image_id": image["id"]}, format="json")
            self.assertEqual(stolen.status_code, 400)
