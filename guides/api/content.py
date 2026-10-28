"""Serializers and save logic for the content of a guide: images and the elements a guide is
built from (see docs/guide-types.md for the field contract).

Every element accepts an optional `id`: with an id the existing element is updated, without
one a new element is created, and elements that are no longer sent are deleted. Ids that
belong to another guide are rejected. The order of the list is the order of the guide.
"""

from urllib.parse import urlsplit

from django.db.models import Q
from rest_framework import serializers

from ..models import ElementKind, GuideElement, GuideImage, GuideType, ImageKind
from ..templatetags.guide_extras import render_markdown


def markdown(max_length):
    """An optional Markdown field (empty string when missing)."""
    return serializers.CharField(max_length=max_length, required=False, allow_blank=True, default="")


class MarkdownHtmlMixin:
    """Adds `<field>_html` (sanitized HTML) for every field named in `markdown_fields`."""

    markdown_fields = ()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for name in self.markdown_fields:
            data[f"{name}_html"] = str(render_markdown(data.get(name) or ""))
        return data


# --- Images -------------------------------------------------------------------


class GuideImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = GuideImage
        fields = ["id", "url", "alt", "caption", "kind", "width", "height"]

    def get_url(self, obj):
        return f"/api/images/{obj.pk}/"


ALLOWED_IMAGE_FORMATS = {"PNG": "image/png", "JPEG": "image/jpeg", "GIF": "image/gif", "WEBP": "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class GuideImageUploadSerializer(serializers.Serializer):
    file = serializers.ImageField()
    alt = serializers.CharField(max_length=200)
    caption = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    kind = serializers.ChoiceField(choices=ImageKind.choices, required=False, allow_blank=True, default="")

    def validate_file(self, upload):
        if upload.size > MAX_IMAGE_BYTES:
            raise serializers.ValidationError("The image must be 5 MB or smaller.")
        # ImageField has opened the file with Pillow; only plain raster formats are allowed
        image_format = getattr(getattr(upload, "image", None), "format", None)
        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise serializers.ValidationError("Allowed formats are PNG, JPEG, GIF and WebP.")
        return upload


# --- Elements -------------------------------------------------------------------

K = ElementKind
# Longest main text of each kind
TEXT_LIMITS = {
    K.SECTION: 160, K.STEP: 160, K.HEADING: 160, K.DIVIDER: 0, K.TEXT: 5000, K.LIST: 2000,
    K.CHECKLIST: 2000, K.QUOTE: 1000, K.LINK: 120, K.TABLE: 200, K.COLLAPSIBLE: 200,
    K.IMPORTANT: 1000, K.ERROR: 1000, K.TIP: 1000, K.NOTE: 1000, K.RESULT: 1000,
    K.IMAGE: 200, K.DIAGRAM: 200, K.TERMINAL: 4000, K.CODE: 4000, K.COMPARE: 1000, K.DOWNLOAD: 120,
}
MARKDOWN_KINDS = {K.TEXT, K.IMPORTANT, K.ERROR, K.TIP, K.NOTE, K.RESULT, K.QUOTE}
MAX_ELEMENTS = 300


def _short(value, limit, label):
    value = "" if value is None else str(value)
    if len(value) > limit:
        raise serializers.ValidationError({"data": f"{label} must be {limit} characters or fewer."})
    return value


def _url(value):
    value = _short(value, 500, "The address").strip()
    if value and (urlsplit(value).scheme not in ("http", "https") or not urlsplit(value).netloc):
        raise serializers.ValidationError({"data": "The address must start with http:// or https://."})
    return value


def _fence(text, language):
    """Markdown code fence that the text cannot end early."""
    longest = max((len(run) for run in text.replace("\n", " ").split(" ") if run and set(run) == {"`"}), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text}\n{fence}"


def clean_data(kind, data):
    """The extra data of an element, reduced to what its kind uses (unknown keys are dropped)."""
    data = data if isinstance(data, dict) else {}
    if kind == K.QUOTE:
        return {"source": _short(data.get("source"), 120, "The source")}
    if kind in (K.LINK, K.DOWNLOAD):
        return {"url": _url(data.get("url"))}
    if kind == K.COLLAPSIBLE:
        return {"body": _short(data.get("body"), 3000, "The text")}
    if kind == K.CODE:
        return {"language": _short(data.get("language"), 30, "The language").strip()}
    if kind == K.COMPARE:
        return {
            "wrong": _short(data.get("wrong"), 3000, "The wrong example"),
            "right": _short(data.get("right"), 3000, "The right example"),
            "language": _short(data.get("language"), 30, "The language").strip(),
        }
    if kind == K.DIAGRAM:
        nodes = [_short(n, 60, "A box").strip() for n in (data.get("nodes") or []) if str(n).strip()]
        if len(nodes) > 12:
            raise serializers.ValidationError({"data": "A diagram has at most 12 boxes."})
        return {"nodes": nodes}
    if kind == K.TABLE:
        rows = data.get("rows") or []
        if not isinstance(rows, list) or len(rows) > 20:
            raise serializers.ValidationError({"data": "A table has at most 20 rows."})
        cleaned = [[_short(c, 200, "A cell") for c in row] for row in rows if isinstance(row, list)]
        width = max((len(row) for row in cleaned), default=0)
        if width > 8:
            raise serializers.ValidationError({"data": "A table has at most 8 columns."})
        return {"rows": [row + [""] * (width - len(row)) for row in cleaned]}
    return {}


def element_html(kind, text, data):
    """Sanitized HTML of an element's main text (empty when the kind shows no text as HTML)."""
    if kind in MARKDOWN_KINDS:
        return str(render_markdown(text))
    if kind == K.LIST:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return str(render_markdown("\n".join(f"- {line}" for line in lines)))
    if kind == K.TERMINAL:
        return str(render_markdown(_fence(text, "console"))) if text.strip() else ""
    if kind == K.CODE:
        return str(render_markdown(_fence(text, data.get("language") or "text"))) if text.strip() else ""
    if kind == K.COLLAPSIBLE:
        return str(render_markdown(data.get("body", "")))
    return ""


class ElementSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    kind = serializers.ChoiceField(choices=ElementKind.choices)
    text = serializers.CharField(max_length=5000, required=False, allow_blank=True, default="", trim_whitespace=False)
    data = serializers.JSONField(required=False, default=dict)
    image_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    image = GuideImageSerializer(read_only=True)

    class Meta:
        model = GuideElement
        fields = ["id", "kind", "text", "data", "image_id", "image"]

    def validate(self, attrs):
        kind = attrs["kind"]
        text = attrs.get("text", "")
        limit = TEXT_LIMITS[kind]
        if len(text) > limit:
            raise serializers.ValidationError({"text": f"The text must be {limit} characters or fewer."})
        if kind not in (K.TERMINAL, K.CODE):
            attrs["text"] = text.strip()
        attrs["data"] = clean_data(kind, attrs.get("data"))
        if kind != K.IMAGE:
            attrs["image_id"] = None
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        extra = dict(data["data"])
        if instance.kind == K.COMPARE:
            language = extra.get("language") or "text"
            for side in ("wrong", "right"):
                text = extra.get(side, "")
                extra[f"{side}_html"] = str(render_markdown(_fence(text, language))) if text.strip() else ""
        data["data"] = extra
        data["html"] = element_html(instance.kind, instance.text, instance.data)
        return data


# --- Rules per guide type -----------------------------------------------------

TYPE_BLOCKS = {
    GuideType.PAGE: {"elements"},
    GuideType.FREE: {"steps"},
}
ALL_BLOCKS = set().union(*TYPE_BLOCKS.values())


def validate_for_type(attrs, guide_type, creating):
    """Check that only the content of `guide_type` is sent. Nothing is required: an empty guide is fine."""
    errors = {}
    for name in ALL_BLOCKS - TYPE_BLOCKS[guide_type]:
        if attrs.get(name):
            errors[name] = f"The guide type “{GuideType(guide_type).label}” has no such content."
    if errors:
        raise serializers.ValidationError(errors)


# --- Saving -------------------------------------------------------------------


def resolve_image(guide, user, image_id, label):
    """The image `image_id` if this user may use it for this guide (attaching it), else an error."""
    if image_id is None:
        return None
    image = GuideImage.objects.filter(pk=image_id).filter(
        Q(guide=guide) | Q(guide__isnull=True, uploaded_by=user)
    ).first()
    if image is None:
        raise serializers.ValidationError({label: f"Image {image_id} is not available."})
    if image.guide_id is None:
        image.guide = guide
        image.save(update_fields=["guide"])
    return image


def save_elements(guide, items, user):
    """Write the elements of the guide in the order they were sent."""
    existing = {obj.id: obj for obj in guide.elements.all()}
    keep = set()
    for position, item in enumerate(items, start=1):
        item_id = item.get("id")
        obj = None
        if item_id is not None:
            obj = existing.get(item_id)
            if obj is None:
                raise serializers.ValidationError({"elements": f"Element {item_id} does not belong to this guide."})
        values = {
            "guide": guide,
            "order": position,
            "kind": item["kind"],
            "text": item.get("text", ""),
            "data": item.get("data", {}),
            "image": resolve_image(guide, user, item.get("image_id"), "elements"),
        }
        if obj is None:
            obj = GuideElement.objects.create(**values)
        else:
            for name, value in values.items():
                setattr(obj, name, value)
            obj.save()
        keep.add(obj.id)
    for obj_id, obj in existing.items():
        if obj_id not in keep:
            obj.delete()


def save_blocks(guide, data, user):
    """Write the element list when it is present in `data` (validated)."""
    if "elements" in data:
        save_elements(guide, data["elements"], user)
