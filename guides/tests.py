from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Guide, Step
from .templatetags.guide_extras import render_markdown


class GuideTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("mel", password="geheim-12345")
        self.category = Category.objects.create(name="Technik")
        self.guide = Guide.objects.create(
            title="Python einrichten", category=self.category, summary="Kurz erklärt"
        )
        Step.objects.create(guide=self.guide, order=1, title="Ordner", body="`mkdir x`")

    def test_slug_is_generated_and_unique(self):
        second = Guide.objects.create(title="Python einrichten")
        self.assertEqual(self.guide.slug, "python-einrichten")
        self.assertEqual(second.slug, "python-einrichten-2")

    def test_home_and_detail_render(self):
        self.assertContains(self.client.get(reverse("guides:home")), "Python einrichten")
        response = self.client.get(self.guide.get_absolute_url())
        self.assertContains(response, "application/ld+json")
        self.assertContains(response, "<code>mkdir x</code>", html=True)

    def test_search_and_htmx_fragment(self):
        response = self.client.get(reverse("guides:home"), {"q": "mkdir"}, HTTP_HX_REQUEST="true")
        self.assertContains(response, "Python einrichten")
        self.assertNotContains(response, "<html")
        empty = self.client.get(reverse("guides:home"), {"q": "gibtsnicht"})
        self.assertContains(empty, "No guides found")

    def test_pdf_download(self):
        response = self.client.get(reverse("guides:pdf", args=[self.guide.slug]))
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_edit_requires_login(self):
        response = self.client.get(reverse("guides:create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_create_guide_with_steps_and_history(self):
        self.client.login(username="mel", password="geheim-12345")
        data = {
            "title": "Neuer Guide",
            "category": self.category.pk,
            "summary": "Test",
            "change_comment": "Erste Version",
            "steps-TOTAL_FORMS": "1",
            "steps-INITIAL_FORMS": "0",
            "steps-MIN_NUM_FORMS": "0",
            "steps-MAX_NUM_FORMS": "1000",
            "steps-0-order": "1",
            "steps-0-title": "Schritt eins",
            "steps-0-body": "Text",
        }
        response = self.client.post(reverse("guides:create"), data)
        guide = Guide.objects.get(title="Neuer Guide")
        self.assertRedirects(response, guide.get_absolute_url())
        self.assertEqual(guide.created_by, self.user)
        self.assertEqual(guide.steps.count(), 1)
        record = guide.history.first()
        self.assertEqual(record.history_change_reason, "Erste Version")
        self.assertEqual(record.history_user, self.user)
        self.assertEqual(self.client.get(reverse("guides:history", args=[guide.slug])).status_code, 200)

    def test_markdown_is_sanitized(self):
        html = render_markdown("Hallo <script>alert(1)</script> [x](javascript:alert(1))")
        self.assertNotIn("<script", html)
        self.assertNotIn("javascript:", html)

    def test_fenced_code_is_highlighted_and_sanitized(self):
        html = render_markdown("```python\nprint('safe')\n```")
        self.assertIn('class="codehilite"', html)
        self.assertIn('class="nb"', html)
        self.assertIn('class="s1"', html)
        self.assertIn("print", html)
        self.assertNotIn("<script", html)

    def test_text_styles_keep_palette_classes_only(self):
        html = render_markdown(
            'A <span class="c-teal">teal</span>, <span class="h-yellow">marked</span>, '
            '<span class="f-hand c-coral">hand</span> and <span class="c-teal fixed-overlay">odd</span> '
            'and <span class="btn">other</span> and <span style="color:red" onclick="x()">style</span>'
        )
        self.assertIn('<span class="c-teal">teal</span>', html)
        self.assertIn('<span class="h-yellow">marked</span>', html)
        self.assertIn('<span class="f-hand c-coral">hand</span>', html)
        self.assertIn('<span class="c-teal">odd</span>', html)  # unknown class dropped, known kept
        self.assertNotIn('btn', html)
        self.assertNotIn('style=', html)
        self.assertNotIn('onclick', html)

    def test_text_styles_work_around_markdown(self):
        html = render_markdown('Press <span class="f-code h-blue">**Ctrl + S**</span> to save')
        self.assertIn('<span class="f-code h-blue"><strong>Ctrl + S</strong></span>', html)

    def test_table_of_contents_links_target_markdown_headings(self):
        html = render_markdown(
            "[First section](#first-section)\n\n"
            "## First section\n\n"
            "[Unsafe](javascript:alert(1))"
        )
        self.assertIn('<a href="#first-section"', html)
        self.assertIn('<h2 id="first-section">First section</h2>', html)
        self.assertNotIn("javascript:", html)

    def test_sitemap(self):
        response = self.client.get(reverse("sitemap"))
        self.assertContains(response, self.guide.slug)


class DefaultCategoryTests(TestCase):
    def test_default_categories_exist_after_migrations(self):
        self.assertTrue(Category.objects.filter(slug="other").exists())
