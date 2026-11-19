# Dependencies

## Python packages

Installed with `pip install -r requirements.txt`:

| Package | Version | Purpose |
|---|---|---|
| Django | 6.1.1 | Web framework |
| djangorestframework | 3.18.1 | REST API |
| djangorestframework-simplejwt | 5.5.1 | JWT authentication with token blacklist (installs PyJWT) |
| django-cors-headers | 4.9.0 | CORS for local development |
| django-simple-history | 3.13.0 | Edit history |
| Markdown | 3.11 | Markdown rendering |
| mammoth | 1.13.0 | Word (.docx) attachment previews |
| Pygments | 2.19.2 | Syntax highlighting for fenced code blocks |
| nh3 | 0.3.7 | HTML sanitizing |
| weasyprint | 70.0 | PDF export (preferred; needs GTK/Pango, often missing on Windows) |
| xhtml2pdf | 0.2.21 | PDF export (fallback, pure Python) |
| whitenoise | 6.12.0 | Static files in production |
| gunicorn | 26.2.0 | Production server (Linux only, `requirements-prod.txt`) |

## Node packages

Installed with `npm install` in `frontend/`:

| Package | Version | Purpose |
|---|---|---|
| nuxt | ^4.5.2 | Frontend framework with server-side rendering |
| vue | ^3.5.43 | UI library |
| vue-router | ^5.3.1 | Routing |
| @tiptap/vue-3, @tiptap/starter-kit, @tiptap/pm, @tiptap/extension-table, @tiptap/extensions | 3.31.4 | Rich-text editor of the free guide |
| turndown, turndown-plugin-gfm | 7.2.4, 1.0.2 | Converts the editor's HTML to Markdown |
| @fontsource-variable/plus-jakarta-sans, @fontsource-variable/jetbrains-mono, @fontsource-variable/source-serif-4, @fontsource-variable/caveat | 5.x | Self-hosted fonts (no requests to Google): interface, code and small labels, reading text, handwriting style |
| typescript | ^5.9.3 | Types (dev) |
| vue-tsc | ^3.3.12 | Type checking (dev) |
| vitest, @vitejs/plugin-vue, @vue/test-utils, happy-dom | ^5.1, ^6.0, ^2.6, ^21 | Frontend tests (dev, see [tests.md](tests.md)) |
