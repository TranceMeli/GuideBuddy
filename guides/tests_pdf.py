import unittest
from unittest import mock

from django.test import TestCase

from . import pdf
from .models import Guide, Step


try:
    import weasyprint  # noqa: F401

    HAS_WEASYPRINT = True
except (ImportError, OSError):  # ohne GTK/Pango (z. B. unter Windows)
    HAS_WEASYPRINT = False


class PdfTests(TestCase):
    def setUp(self):
        self.guide = Guide.objects.create(title="Größe & Ärger", summary="Prüfung für Öl")
        Step.objects.create(
            guide=self.guide, order=1, title="Schritt eins",
            body="Text mit **fett** und Umlauten äöüß.\n\n```\nprint('hi')\n```\n\n- a\n- b\n\n| x | y |\n|---|---|\n| 1 | 2 |",
        )
        self.url = f"/api/guides/{self.guide.slug}/pdf/"

    def test_default_engine_returns_pdf_download(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn(f'{self.guide.slug}.pdf', response["Content-Disposition"])

    def test_fallback_to_xhtml2pdf_without_gtk(self):
        with mock.patch.object(pdf, "_weasyprint", side_effect=OSError("libgobject fehlt")):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertGreater(len(response.content), 1000)

    def test_503_when_no_engine_works(self):
        with mock.patch.object(pdf, "_weasyprint", side_effect=OSError("x")), mock.patch.object(
            pdf, "_xhtml2pdf", side_effect=ImportError("x")
        ):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)

    def test_unknown_guide_is_404(self):
        self.assertEqual(self.client.get("/api/guides/gibts-nicht/pdf/").status_code, 404)

    def test_online_link_points_to_frontend(self):
        from django.template.loader import render_to_string

        html = render_to_string(
            "guides/guide_pdf_simple.html",
            {"guide": self.guide, "steps": [], "frontend_url": "https://guidebuddy.example"},
        )
        self.assertIn(f"https://guidebuddy.example/guides/{self.guide.slug}", html)

    def test_xhtml2pdf_does_not_fetch_external_images(self):
        Step.objects.create(
            guide=self.guide, order=2, title="Bild",
            body="![x](http://127.0.0.1:9/geheim.png) ![y](/etc/passwd)",
        )
        with mock.patch.object(pdf, "_weasyprint", side_effect=OSError("x")), mock.patch(
            "urllib.request.urlopen", side_effect=AssertionError("Netzwerkzugriff!")
        ) as urlopen:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        urlopen.assert_not_called()

    @unittest.skipUnless(HAS_WEASYPRINT, "WeasyPrint ist hier nicht nutzbar")
    def test_weasyprint_only_allows_data_urls(self):
        fake_html = mock.MagicMock()
        fake_html.return_value.write_pdf.return_value = b"%PDF-fake"
        with mock.patch("weasyprint.HTML", fake_html):
            self.assertEqual(pdf._weasyprint("<p>x</p>", "http://testserver/"), b"%PDF-fake")
        fetcher = fake_html.call_args.kwargs["url_fetcher"]
        with self.assertRaises(ValueError):
            fetcher.fetch("http://169.254.169.254/latest/meta-data/")
        with self.assertRaises(ValueError):
            fetcher.fetch("file:///etc/passwd")
