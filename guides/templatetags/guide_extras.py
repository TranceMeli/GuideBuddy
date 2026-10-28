import re

import markdown as md
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = {
    "p", "br", "hr", "strong", "em", "code", "pre", "span", "div", "blockquote",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5",
    "a", "img", "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "id"},
    "img": {"src", "alt", "title"},
    "code": {"class"},
    "div": {"class"},
    "h1": {"id"},
    "h2": {"id"},
    "h3": {"id"},
    "h4": {"id"},
    "h5": {"id"},
    "pre": {"class"},
    "span": {"class"},
}


# Text styles authors can pick (frontend/app/utils/textStyles.ts has the same list). Content
# only carries these names, never colours or font names: the themes decide how they look.
# Colours and fonts show in the standard look; Mono turns highlights light gray and keeps fonts.
TEXT_STYLE_CLASSES = {
    "c-blue", "c-teal", "c-coral", "c-violet", "c-gray",  # text colour
    "h-yellow", "h-teal", "h-blue", "h-pink",  # highlight
    "f-serif", "f-hand", "f-code",  # font
}
# Class names of the code highlighter (Pygments): "k", "nb", "s2", "c1", "kn" …
_CODE_TOKEN = re.compile(r"^[a-z]{1,2}[0-9]?$")


def _attribute_filter(tag, attribute, value):
    """Keeps only known class names on <span>; other attributes pass unchanged."""
    if tag != "span" or attribute != "class":
        return value
    kept = [c for c in value.split() if c in TEXT_STYLE_CLASSES or _CODE_TOKEN.match(c)]
    return " ".join(kept) or None


def sanitize_html(html):
    """The one place where HTML from Markdown or uploads is cleaned."""
    return nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, attribute_filter=_attribute_filter)


@register.filter
def render_markdown(text):
    """Markdown -> HTML, then sanitized (nh3) so no script slips through."""
    html = md.markdown(
        text or "",
        extensions=[
            "fenced_code",
            "codehilite",
            "tables",
            "sane_lists",
            "toc",
        ],
        extension_configs={
            "codehilite": {
                "guess_lang": False,
                "noclasses": False,
                "use_pygments": True,
            }
        },
    )
    return mark_safe(sanitize_html(html))
