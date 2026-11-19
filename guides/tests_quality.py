"""Tests that guard things which are easy to forget when something is added: every kind of element
is handled everywhere, the sample guides follow the writing rules, the docs point to files that
exist, the colours stay readable, and forms get their errors per field."""

import re
import subprocess
import sys
from pathlib import Path

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APITestCase

from .api.content import MARKDOWN_KINDS, TEXT_LIMITS, clean_data
from .management.commands.seed_samples import SAMPLES
from .models import ElementKind, Guide, GuideElement
from .pdf_elements import BOX, render_elements_html

ROOT = Path(__file__).resolve().parent.parent
NOTICES = {"important", "warning", "danger", "error", "tip", "note", "result"}

# The least a kind needs to be valid: its text, or the data it keeps instead
MINIMAL = {
    "link": ("The Python downloads page", {"url": "https://www.python.org/downloads/"}),
    "download": ("Download the template", {"url": "https://example.com/template.pdf"}),
    "table": ("", {"rows": [["Phase", "Time"], ["Bake", "20 minutes"]]}),
    "collapsible": ("A question", {"body": "The answer."}),
    "diagram": ("A flow", {"nodes": ["Mix", "Bake"]}),
    "compare": ("Which one?", {"wrong": "a", "right": "b", "language": ""}),
    "code": ("print('hi')", {"language": "python"}),
    "quote": ("A quote", {"source": "Somebody"}),
}


class EveryKindIsHandledTests(TestCase):
    def test_every_kind_has_a_text_limit(self):
        missing = [kind for kind in ElementKind if kind not in TEXT_LIMITS]
        self.assertEqual(missing, [], "a new kind needs a limit in guides/api/content.py")

    def test_every_notice_is_markdown_and_has_a_label_in_the_pdf(self):
        self.assertEqual(set(BOX), {ElementKind(k) for k in NOTICES})
        self.assertTrue(NOTICES <= {str(k) for k in MARKDOWN_KINDS})

    def test_every_kind_can_be_cleaned_and_rendered_in_the_pdf(self):
        guide = Guide.objects.create(title="All kinds", guide_type="page")
        for order, kind in enumerate(ElementKind, start=1):
            text, data = MINIMAL.get(kind.value, ("Some text", {}))
            if kind == ElementKind.DIVIDER:
                text = ""
            GuideElement.objects.create(guide=guide, order=order, kind=kind, text=text, data=clean_data(kind, data))
        html = render_elements_html(guide)
        for label in BOX.values():
            self.assertIn(f"<strong>{label}</strong>", html)
        self.assertIn("<table>", html)

    def test_status_boxes_have_their_own_colours_in_the_pdf(self):
        # tip and note stay in the neutral box; the boxes with a warning meaning are coloured
        template = (ROOT / "guides" / "templates" / "guides" / "guide_pdf.html").read_text(encoding="utf8")
        for name in ("important", "warning", "danger", "error", "result"):
            self.assertIn(f".box-{name}", template, f"the PDF has no colour for the {name} box")


def block_of_each_step(elements):
    """The elements after each step, up to the next step or section."""
    kinds = [e["kind"] for e in elements]
    steps = [i for i, kind in enumerate(kinds) if kind == "step"]
    for i in steps:
        rest = kinds[i + 1:]
        end = next((n for n, kind in enumerate(rest) if kind in ("step", "section")), len(rest))
        yield elements[i]["text"], rest[:end]


class SampleGuidesFollowTheWritingRulesTests(SimpleTestCase):
    """The sample guides show what a good guide looks like, so they follow the rules themselves."""

    def test_the_goal_comes_first(self):
        for sample in SAMPLES:
            self.assertEqual(sample["elements"][0]["kind"], "text", sample["title"])

    def test_every_step_says_what_readers_should_see(self):
        for sample in SAMPLES:
            for title, block in block_of_each_step(sample["elements"]):
                self.assertIn("result", block, f"{sample['title']}: step “{title}” has no expected result")

    def test_a_step_names_one_action(self):
        two_actions = re.compile(r"\band\s+(then\s+)?(add|mix|stir|fold|press|click|open|close|cut|wait|rest|heat|cook|bake|boil|pour|remove|turn|select|install|save|run|check)\b", re.I)
        for sample in SAMPLES:
            for title, _ in block_of_each_step(sample["elements"]):
                self.assertIsNone(two_actions.search(title), f"{sample['title']}: “{title}” may be two actions")

    def test_the_guide_ends_with_an_outcome_and_a_way_to_fix_problems(self):
        for sample in SAMPLES:
            elements = sample["elements"]
            sections = [e["text"] for e in elements if e["kind"] == "section"]
            self.assertIn("Outcome", sections, sample["title"])
            self.assertIn("If something goes wrong", sections, sample["title"])
            titles = [e.get("text", "") for e in elements]
            after_outcome = elements[titles.index("Outcome") + 1]
            self.assertEqual(after_outcome["kind"], "result", sample["title"])
            trouble = next(e for e in elements if e["kind"] == "table" and e["data"]["rows"][0][0] == "If you see …")
            self.assertEqual(trouble["data"]["rows"][0], ["If you see …", "Then …"])

    def test_a_warning_never_comes_after_the_last_step(self):
        for sample in SAMPLES:
            kinds = [e["kind"] for e in sample["elements"]]
            last_step = max(i for i, kind in enumerate(kinds) if kind == "step")
            late = [kind for kind in kinds[last_step:] if kind in ("warning", "danger")]
            self.assertEqual(late, [], sample["title"])

    def test_materials_come_with_quantities_where_they_are_ingredients(self):
        sourdough = next(s for s in SAMPLES if s["title"].startswith("Bake Sourdough"))
        checklist = next(e for e in sourdough["elements"] if e["kind"] == "checklist")
        self.assertTrue(all(re.search(r"\d", line) or "oven" in line for line in checklist["text"].splitlines()))


class DocsPointToFilesThatExistTests(SimpleTestCase):
    def test_links_and_images_in_the_readme_and_the_docs_exist(self):
        files = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
        broken = []
        for path in files:
            text = path.read_text(encoding="utf8")
            targets = re.findall(r"\]\(([^)\s]+)\)", text) + re.findall(r'src="([^"]+)"', text)
            for target in targets:
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                if not (path.parent / target.split("#")[0]).exists():
                    broken.append(f"{path.name}: {target}")
        self.assertEqual(broken, [])

    def test_the_colour_pairs_of_the_design_tokens_pass_wcag_aa(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_contrast.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)


class RegisterErrorsComeFieldByFieldTests(APITestCase):
    """The register form shows each message under its field, so the API must name the field."""

    def setUp(self):
        cache.clear()

    def register(self, **fields):
        data = {"username": "anna", "email": "anna@example.com", "password": "a-long-enough-password-1", "accept_terms": True, "website": "", "captcha_token": ""}
        return self.client.post("/api/auth/register/", {**data, **fields}, format="json")

    def test_an_invalid_address_is_answered_on_the_email_field(self):
        response = self.register(email="anna@example")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(all(isinstance(message, str) for message in response.data["email"]))
        self.assertEqual(User.objects.count(), 0)

    def test_a_weak_password_is_answered_on_the_password_field(self):
        response = self.register(password="short")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(all(isinstance(message, str) for message in response.data["password"]))
        self.assertEqual(User.objects.count(), 0)

    def test_missing_terms_are_reported_on_their_own_field(self):
        response = self.register(accept_terms=False)
        self.assertEqual(response.status_code, 400)
        self.assertIn("accept_terms", response.data)
