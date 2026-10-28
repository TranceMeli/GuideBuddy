# Guides, elements and fields

GuideBuddy uses **single sourcing**: authors build a guide from elements, and one template
renders it for the web and PDF. Authors never choose colors, fonts or layout.

This document is the contract between the guide builder (Nuxt), the API (DRF serializers) and
the output templates. Field names below are the API field names.

## Two kinds of guide

| Type (`guide_type`) | What it is |
|---|---|
| `page` – Guide | An ordered list of **elements**. This is what the guide builder creates. |
| `free` – File or text | A finished text (title and body per step) and/or one attached file. Created with `/guides/new?file=1`. |

The type is set when a guide is created and **cannot be changed later**.

## Common fields

| Field | Type | Required | Limits | Notes |
|---|---|---|---|---|
| `title` | text | yes | 160 | States the result: "Change a bike inner tube" |
| `subtitle` | text | no | 200 | One line under the title |
| `language` | choice | no | – | `en` (default) is the only language for now |
| `summary` | plain text | no | 300 | Card text on the overview, meta description |
| `category_id` | id | yes¹ | – | One of the fixed categories |
| `difficulty` | choice | no | – | `beginner`, `intermediate`, `advanced` |
| `duration_minutes` | integer | no | 1–1,440 | Estimated time |
| `cover_image_id` | id | no | – | Write-only: an image uploaded to this guide, shown on the overview cards |
| `change_comment` | text | no | 200 | Write-only, shown in the history |

¹ Required in the editor as soon as categories exist; the API accepts a guide without one.

## `page` guides: elements

`elements` is a list of up to 300 elements in the order readers see them. **Nothing is
required**: an empty guide is valid, and there is no fixed structure. Every element has:

| Field | Notes |
|---|---|
| `id` | On update: the existing element is changed. Without an id a new one is created; elements that are no longer sent are deleted. |
| `kind` | One of the kinds below. |
| `text` | The main text (title, Markdown, caption …; limit per kind). |
| `data` | What the kind needs besides (below). Unknown keys are dropped. |
| `image_id` | Write-only, only for `image`. Read: `image` with `url`, `alt`, `caption`, `kind`. |
| `html` | Read-only: sanitized HTML of the main text where the kind has one. |

| Kind | `text` | `data` | Readers see |
|---|---|---|---|
| `section` | title (160) | – | label "Section n", heading with a rule; also in the contents |
| `step` | title (160) | – | numbered badge readers can tick off (kept in their browser) |
| `heading` | heading (160) | – | a smaller heading |
| `divider` | – | – | a line |
| `text` | Markdown (5,000) | – | a paragraph |
| `list` | one item per line (2,000) | – | a bulleted list |
| `checklist` | one item per line (2,000) | – | checkboxes |
| `quote` | Markdown (1,000) | `source` (120) | an indented quote |
| `link` | link text (120) | `url` (http/https) | a link on its own line |
| `table` | – | `rows`: up to 20 × 8 cells of 200; the first row is the heading | a table (cards on phones) |
| `collapsible` | title (200) | `body` Markdown (3,000) | a line that opens |
| `important` | Markdown (1,000) | – | yellow box "Important" |
| `error` | Markdown (1,000) | – | red box "Error" |
| `tip` / `note` | Markdown (1,000) | – | blue box |
| `result` | Markdown (1,000) | – | green box "Expected result" |
| `image` | – | – | the picture with a numbered caption (Figure n) |
| `diagram` | caption (200) | `nodes`: up to 12 boxes of 60 | boxes with arrows |
| `terminal` | commands and answers (4,000) | – | dark block; error lines red, success lines green |
| `code` | code (4,000) | `language` (30) | code block |
| `compare` | explanation (1,000) | `wrong`, `right` (3,000 each), `language` | two blocks marked Wrong and Right |
| `download` | button label (120) | `url` (http/https) | a button with a download icon |

Markdown kinds (`text`, `important`, `error`, `tip`, `note`, `result`, `quote`) accept bold,
italic, `code`, lists, links and the text styles below. The server sanitizes all of it.

## Images

Images are uploaded separately (`POST /api/images/`) before the guide is saved and referenced
by `image_id`. Alt text is required (200). `kind` (photo, screenshot, mockup, diagram) and
`caption` (200) are shown under the image, so a drawn interface is never passed off as a
screenshot. An unused image is private to its uploader.

## Text styles

Any Markdown field can carry three kinds of text style, written as `<span class="…">` around
the text (the only HTML the server keeps, and only these class names):

| Kind | Classes | Shown as |
|---|---|---|
| Text colour | `c-blue`, `c-teal`, `c-coral`, `c-violet`, `c-gray` | coloured text |
| Highlight | `h-yellow`, `h-teal`, `h-blue`, `h-pink` | tinted background |
| Font | `f-serif`, `f-hand`, `f-code` | font |

Colour is decoration only: meaning is carried by the notice boxes, never by a colour.

## Notice boxes

Fixed meaning, always an icon and a word as well as the colour:

| Box | Kind | Colour |
|---|---|---|
| Important | `important` | yellow |
| Error | `error` | red |
| Tip | `tip` | blue |
| Note | `note` | blue |
| Expected result | `result` | green |

## Search and PDF

Search looks in the title, summary, the text of elements and the steps of free guides. The
PDF is built from the elements in order (`guides/pdf_elements.py`); images are linked by their
address.
