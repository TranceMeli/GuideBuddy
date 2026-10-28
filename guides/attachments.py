"""Previews for uploaded files.

- The browser shows PDFs and images itself (embedded via ?inline=1).
- Word, Markdown, text and CSV are converted to sanitized HTML here.
- Excel and PowerPoint have no preview (download only).
"""

import csv
import io
import logging
from html import escape
from pathlib import PurePosixPath

import mammoth
from django.core.cache import cache

from .templatetags.guide_extras import render_markdown, sanitize_html

logger = logging.getLogger(__name__)

INLINE_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
HTML_PREVIEW = {".docx", ".md", ".txt", ".csv"}

# Do not put huge text files into the page completely
MAX_TEXT_BYTES = 300 * 1024
MAX_CSV_ROWS = 500


def extension(name):
    return PurePosixPath(name).suffix.lower()


def attachment_kind(name):
    """'pdf', 'image', 'html' (preview as HTML) or 'none' (download only)."""
    ext = extension(name)
    if ext == ".pdf":
        return "pdf"
    if ext in INLINE_TYPES:
        return "image"
    if ext in HTML_PREVIEW:
        return "html"
    return "none"


def _read_text(fileobj):
    data = fileobj.read(MAX_TEXT_BYTES + 1)
    truncated = len(data) > MAX_TEXT_BYTES
    text = data[:MAX_TEXT_BYTES].decode("utf-8-sig", errors="replace")
    return text, truncated


def _csv_table(text):
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.reader(io.StringIO(text), dialect))[:MAX_CSV_ROWS]
    if not rows:
        return ""
    head, *body = rows
    html = ["<table><thead><tr>"]
    html += [f"<th>{escape(cell)}</th>" for cell in head]
    html.append("</tr></thead><tbody>")
    for row in body:
        html.append("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>")
    html.append("</tbody></table>")
    return "".join(html)


def build_preview_html(fileobj, name):
    """Sanitized HTML for Word/Markdown/text/CSV, otherwise ''."""
    ext = extension(name)
    try:
        if ext == ".docx":
            # Leave out images from Word files (they would be embedded as huge data: URLs)
            result = mammoth.convert_to_html(fileobj, convert_image=mammoth.images.img_element(lambda image: {}))
            html = result.value
        else:
            text, truncated = _read_text(fileobj)
            if ext == ".md":
                html = str(render_markdown(text))
            elif ext == ".csv":
                html = _csv_table(text)
            else:
                html = f"<pre>{escape(text)}</pre>"
            if truncated:
                html += "<p><em>… The file is longer. Download it to see everything.</em></p>"
    except Exception:  # damaged file: rather no preview than an error
        logger.warning("Preview for %s failed", name, exc_info=True)
        return ""
    return sanitize_html(html)


def stored_preview_html(field_file):
    """Preview of a stored file, cached (file names are unique)."""
    if attachment_kind(field_file.name) != "html":
        return ""
    key = f"attachment-preview:{field_file.name}"
    html = cache.get(key)
    if html is None:
        try:
            with field_file.open("rb") as handle:
                html = build_preview_html(handle, field_file.name)
        except OSError:
            return ""
        cache.set(key, html, 60 * 60 * 24)
    return html

