"""HTML of the elements of a guide for the PDF export (the reading view is rendered by the frontend)."""

from django.utils.html import escape
from django.utils.safestring import mark_safe

from .api.content import element_html
from .models import ElementKind

K = ElementKind
BOX = {K.IMPORTANT: "Important", K.WARNING: "Warning", K.DANGER: "Danger", K.ERROR: "Error", K.TIP: "Tip", K.NOTE: "Note", K.RESULT: "Expected result"}


def _pre(text):
    return f"<pre>{escape(text)}</pre>"


def _one(el, counters):
    kind, data = el.kind, el.data or {}
    text = escape(el.text)
    if kind == K.SECTION:
        counters["section"] += 1
        return f"<h2>{text}</h2>"
    if kind == K.STEP:
        counters["step"] += 1
        return f"<h3>Step {counters['step']}: {text}</h3>"
    if kind == K.HEADING:
        return f"<h4>{text}</h4>"
    if kind == K.DIVIDER:
        return "<hr>"
    if kind in (K.TEXT, K.LIST, K.TERMINAL, K.CODE):
        return element_html(kind, el.text, data)
    if kind == K.CHECKLIST:
        items = "".join(f"<li>&#9744; {escape(line)}</li>" for line in el.text.splitlines() if line.strip())
        return f'<ul style="list-style:none;padding-left:0">{items}</ul>'
    if kind == K.QUOTE:
        source = f"<p><em>{escape(data.get('source', ''))}</em></p>" if data.get("source") else ""
        return f"<blockquote>{element_html(kind, el.text, data)}{source}</blockquote>"
    if kind in (K.LINK, K.DOWNLOAD):
        url = data.get("url", "")
        label = text or escape(url)
        return f'<p><a href="{escape(url)}">{label}</a></p>' if url else f"<p>{label}</p>"
    if kind == K.TABLE:
        rows = data.get("rows") or []
        if not rows:
            return ""
        head = "".join(f"<th>{escape(c)}</th>" for c in rows[0])
        body = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>" for row in rows[1:])
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    if kind == K.COLLAPSIBLE:
        return f"<h4>{text}</h4>{element_html(kind, el.text, data)}"
    if kind in BOX:
        return f'<div class="box box-{kind}"><strong>{BOX[kind]}</strong>{element_html(kind, el.text, data)}</div>'
    if kind == K.IMAGE:
        if not el.image_id:
            return ""
        caption = f"<p><em>{text}</em></p>" if el.text else ""
        return f'<p><img src="/api/images/{el.image_id}/" alt="{escape(el.image.alt)}" style="max-width:100%"></p>{caption}'
    if kind == K.DIAGRAM:
        nodes = data.get("nodes") or []
        flow = " &rarr; ".join(f"<strong>{escape(n)}</strong>" for n in nodes)
        return f"<p>{flow}</p>" + (f"<p><em>{text}</em></p>" if el.text else "")
    if kind == K.COMPARE:
        parts = []
        for label, key in (("Wrong", "wrong"), ("Right", "right")):
            if data.get(key):
                parts.append(f"<p><strong>{label}</strong></p>{_pre(data[key])}")
        return (f"<p>{text}</p>" if el.text else "") + "".join(parts)
    return ""


def render_elements_html(guide):
    counters = {"section": 0, "step": 0}
    return mark_safe("\n".join(_one(el, counters) for el in guide.elements.select_related("image")))
