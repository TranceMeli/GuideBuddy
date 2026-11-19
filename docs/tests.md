# Tests

GuideBuddy has three kinds of checks: backend tests (Django), frontend tests (Vitest) and two scripts for types and colours. Run all of them before a change goes in.

## Running everything

```bash
python manage.py test                # backend, 193 tests, takes a few minutes
python scripts/check_contrast.py     # colour pairs of the design tokens against WCAG AA
cd frontend
npm test                             # frontend, 74 tests, takes a few seconds
npm run typecheck                    # TypeScript and Vue types
```

One backend file or test: `python manage.py test guides.tests_quality` or `python manage.py test guides.tests_quality.DocsPointToFilesThatExistTests`. One frontend file: `npx vitest run tests/elements.test.ts`.

## Backend (`guides/tests*.py`)

Django test cases with a temporary database. API tests use DRF's `APITestCase`.

| File | What it covers |
|---|---|
| `tests.py` | Pages of the older Django frontend and their permissions |
| `tests_accounts.py` | Registration, e-mail confirmation, password reset, account deletion, spam protection |
| `tests_jwt.py` | Login with tokens: rotation, blocklist, revocation on password change and ban |
| `tests_api.py` | Reading and writing guides through the API: list, search, filters, saving, history, attachments, images |
| `tests_types.py` | The elements of a guide: every kind, validation, sanitizing, PDF, the notice levels |
| `tests_comments.py` | Comments on a guide or an element, replies, questions and answers, "Helpful" votes, reports |
| `tests_delete.py` | Who may delete a guide |
| `tests_moderation.py` | Reports, locking guides, banning, the moderator group |
| `tests_lifecycle.py` | Status (archive, restore, outdated), version and contributors, the new report reasons, comment kinds, hiding comments, related guides, search suggestions |
| `tests_pdf.py` | PDF export and its fallback |
| `tests_ops.py` | Backups, clean-up of unconfirmed accounts, the sample guides, deploy checks |
| `tests_quality.py` | Guard tests, see below |

### Guard tests (`tests_quality.py`)

These fail when something is added in one place and forgotten in another.

- **Every kind of element is handled:** each kind has a text limit, can be cleaned and appears in the PDF; the notice boxes have a label and, where they carry a warning meaning, a colour in the PDF.
- **The sample guides follow the writing rules:** the goal comes first, every step ends with an expected result, a step names one action, the guide ends with an outcome and a troubleshooting table, no warning comes after the last step.
- **The documentation points to files that exist:** every relative link and image in `README.md` and `docs/*.md`.
- **The colours stay readable:** runs `scripts/check_contrast.py`.
- **Forms get their errors per field:** the register form shows each message under its field, so the API must name the field. Password rules are checked after the other fields, so a weak password is only reported once e-mail and user name are valid. The form therefore also checks the length itself before asking the server.

## Frontend (`frontend/tests/`)

Vitest. Files that do not need a browser run in Node; component tests start with `// @vitest-environment happy-dom` and use `@vue/test-utils`. Nuxt's auto-imports (`computed`, `useState`, `localKey` …) are provided as globals in `tests/setup.ts`, so the code under test runs without a Nuxt server.

| File | What it covers |
|---|---|
| `elements.test.ts` | The tools (one per kind, unique shortcuts, help texts), blank elements are not saved, the API payload, numbering, the how-to template (order, hints, nothing saved when unused) |
| `publishChecks.test.ts` | The ten suggestions of "Before you publish": one passing and one failing case each |
| `apiErrors.test.ts` | Turning API errors into messages, and into messages per form field |
| `composables.test.ts` | `useToast` (message, link, id, shared between pages) and `useConfirm` (answers, a new question cancels the old one) |
| `FormField.test.ts` | Label, required mark, help text, error text and the `aria-` attributes of an input |
| `BuilderToolbar.test.ts` | The six edit buttons: texts, shortcuts, disabled states, events |
| `lifecycle.test.ts` | Status labels, comment kinds, report reasons, the by-line and the note about outdated guides |
| `placeholders.test.ts` | Category colours and icons of the guide cards, moving items in a list |

## What is not covered

- **No end-to-end tests.** The builder as a whole (undo and redo in `ElementsEditor.vue`, the draft in `StructuredGuideEditor.vue`, tool search in `BuilderPalette.vue`), the dialog and toast components and the comments panel are not tested automatically. They were checked by hand in a browser.
- **No visual tests.** Colour and layout are only checked through the contrast script and by looking at the pages.
- **No tests for accessibility with a screen reader or the keyboard.** The `aria-` wiring of `FormField` is tested, the rest is not.
- **Cloudflare Turnstile and real SMTP delivery** are tested with mocks only.

## Adding a test

- Name a test after what happens, not after the function: `it('keeps an optional link')`.
- When you add a kind of element, a notice level or a documentation file, the guard tests tell you what else needs a change.
- Put pure logic into `frontend/app/utils/` or a composable without Nuxt calls, so it can be tested in Node.
- A bug gets a test that fails first. The how-to template, for example, once saved its troubleshooting table even when unused; `elements.test.ts` now covers it.
