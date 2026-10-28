"""PDF generation for guides.

Prefers WeasyPrint (nice output, page numbers, but needs GTK/Pango, often missing on
Windows). Without it, xhtml2pdf steps in automatically (pure Python, runs everywhere,
simpler layout).

Guide content comes from users. Images in it (`![](http://...)`) must not fetch anything
while the PDF is built, otherwise anyone could make the server request addresses in the
internal network or read local files (SSRF). Only embedded data: URLs are allowed.
"""

import io
import logging

logger = logging.getLogger(__name__)


class PdfUnavailable(Exception):
    """Neither WeasyPrint nor xhtml2pdf can be used."""


def _weasyprint(html, base_url):
    from weasyprint import HTML  # imported here: fails with OSError without GTK
    from weasyprint.urls import URLFetcher

    fetcher = URLFetcher(allowed_protocols={"data"}, allow_redirects=False)
    return HTML(string=html, base_url=base_url, url_fetcher=fetcher).write_pdf()


def _xhtml2pdf(html):
    from xhtml2pdf import pisa
    from xhtml2pdf.config.resources import ResourceAccessPolicy

    # No network, no local files (base_dir=None forbids local reads)
    policy = ResourceAccessPolicy(allow_remote=False, base_dir=None)
    buffer = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8", resource_policy=policy)
    if result.err:
        raise PdfUnavailable("xhtml2pdf could not create the PDF.")
    return buffer.getvalue()


def render_pdf(*, html, simple_html, base_url):
    """Return PDF bytes. `simple_html` is the simpler version for xhtml2pdf."""
    try:
        return _weasyprint(html, base_url)
    except (ImportError, OSError) as error:
        logger.info("WeasyPrint not available (%s), using xhtml2pdf.", error)
    try:
        return _xhtml2pdf(simple_html)
    except ImportError as error:
        raise PdfUnavailable(str(error)) from error
