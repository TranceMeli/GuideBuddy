"""Small helpers about the elements of a guide."""

from .models import ElementKind


def anchor_label(element):
    """A short name for an element ("Step 2: Start the installer"), kept with a comment about it."""
    kind = element.kind
    name = ElementKind(kind).label
    if kind in (ElementKind.SECTION, ElementKind.STEP):
        number = element.guide.elements.filter(kind=kind, order__lte=element.order).count()
        name = f"{name} {number}"
    text = (element.text or "").strip()
    first = text.splitlines()[0] if text else ""
    first = first.replace("*", "").replace("`", "").replace("_", " ").strip()
    if len(first) > 45:
        first = first[:44].rstrip() + "…"
    if not first and element.kind == ElementKind.IMAGE and element.image_id:
        first = element.image.alt[:45]
    label = f"{name}: {first}" if first else name
    return label[:120]
