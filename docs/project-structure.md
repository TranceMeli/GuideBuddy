# Project structure

```text
backend/           Django settings and URLs
guides/            Models, API, permissions, mails, PDF (pdf.py, pdf_elements.py), attachment previews, admin, tests
                   (elements.py: names of elements for comments; tests_comments.py)
  api/             Serializers, views and routes of the REST API
    content.py     Images and the elements of a guide: serializers, rules per kind, saving
  management/      backup_db, cleanup_unverified, seed_demo, seed_samples
frontend/
  app/             Pages, components, composables, layout, styles
    assets/css/    tokens.css (colours, fonts), main.css, templates.css (reading view), guides.css (editors)
    components/    StructuredGuideEditor.vue: the editor page (title, chips, checks, draft);
                   ElementsEditor.vue: the guide builder; builder parts: BuilderShell (layout and
                   side-panel tabs), BuilderToolbar, BuilderPalette, BuilderCard, BuilderPanel,
                   BuilderGap (state in composables/useBuilder.ts);
                   ElementsReader.vue: the reading view of a guide (GuideReader.vue picks it
                   or FreeReader.vue); GuideEditor.vue: the editor for a file or finished text;
                   ReadingBars.vue: slim bar and status bar while reading;
                   GuideComments.vue: comments, replies, questions and answers, Helpful, reports;
                   shared parts: MetaChips, StepBadge, Callout, DataTable, CodeBlock, GuideCard, GuideIcon;
                   forms and feedback: FormField (label, help, error), AppToast, ConfirmDialog
                   (composables useToast, useConfirm); FirstVisitTip: the hint on the first visit
    utils/         elements.ts: the tools, element drafts, the how-to template and the API payload;
                   previewGuide.ts: live preview; publishChecks.ts: the "Before you publish" list;
                   guideLabels.ts, guidePlaceholder.ts, placeholders.ts;
                   lifecycle.ts: status labels, comment kinds, report reasons
  server/          Nuxt server: API proxy, login cookie, sitemap, robots.txt
  tests/           Vitest tests of utils, composables and small components (see tests.md)
scripts/           check_contrast.py: WCAG check of the colour tokens
templates/         Base template of the old Django frontend
static/            Styles of the old Django frontend
docs/              This documentation; screenshots/ for the README
```
