from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from ..attachments import attachment_kind, stored_preview_html
from ..models import Category, Guide, GuideComment, GuideType, Report, Step
from ..permissions import is_moderator, write_denial
from ..templatetags.guide_extras import render_markdown
from .content import (
    ALL_BLOCKS,
    resolve_image,
    ElementSerializer,
    GuideImageSerializer,
    MarkdownHtmlMixin,
    save_blocks,
    validate_for_type,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class StepSerializer(serializers.ModelSerializer):
    # id is optional when writing: with an id the step is updated, without one it is created
    id = serializers.IntegerField(required=False)
    # sanitized HTML, so the frontend never has to filter anything itself
    body_html = serializers.SerializerMethodField()

    class Meta:
        model = Step
        fields = ["id", "order", "title", "body", "body_html"]

    def get_body_html(self, obj):
        return str(render_markdown(obj.body))


class GuideCommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True, default=None)
    body_html = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    kind = serializers.ChoiceField(choices=GuideComment.Kind.choices, required=False, default=GuideComment.Kind.COMMENT)
    # Write: which element or comment this is about (checked against the guide in the view)
    element_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    parent_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    # Read
    element = serializers.IntegerField(source="element_id", read_only=True)
    parent = serializers.IntegerField(source="parent_id", read_only=True)
    by_guide_author = serializers.SerializerMethodField()
    helpful_count = serializers.SerializerMethodField()
    helpful = serializers.SerializerMethodField()
    can_mark_answer = serializers.SerializerMethodField()

    class Meta:
        model = GuideComment
        fields = [
            "id", "author", "body", "body_html", "created_at", "edited_at", "can_edit",
            "kind", "element_id", "parent_id", "element", "anchor", "parent", "is_answer",
            "by_guide_author", "helpful_count", "helpful", "can_mark_answer",
        ]
        read_only_fields = ["id", "author", "body_html", "created_at", "edited_at", "can_edit", "anchor", "is_answer"]

    def _user(self):
        request = self.context.get("request")
        return request.user if request is not None and request.user.is_authenticated else None

    def get_body_html(self, obj):
        return str(render_markdown(obj.body))

    def get_can_edit(self, obj):
        user = self._user()
        return bool(user and (obj.author_id == user.pk or is_moderator(user)))

    def get_by_guide_author(self, obj):
        return obj.author_id is not None and obj.author_id == obj.guide.created_by_id

    def get_helpful_count(self, obj):
        return len(obj.votes.all())

    def get_helpful(self, obj):
        user = self._user()
        return bool(user and any(vote.user_id == user.pk for vote in obj.votes.all()))

    def get_can_mark_answer(self, obj):
        """Replies to a question can be marked by its author, the author of the guide and moderators."""
        user = self._user()
        parent = obj.parent
        if not user or parent is None or parent.kind != GuideComment.Kind.QUESTION:
            return False
        return user.pk in (parent.author_id, obj.guide.created_by_id) or is_moderator(user)


class GuideCommentPreviewSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000, allow_blank=False, trim_whitespace=True)


class GuideAttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, upload):
        if upload.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("The file must be 10 MB or smaller.")

        extension = PurePosixPath(upload.name).suffix.lower()
        signatures = {
            ".pdf": lambda data: data.startswith(b"%PDF-"),
            ".png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
            ".jpg": lambda data: data.startswith(b"\xff\xd8\xff"),
            ".jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
            ".gif": lambda data: data.startswith((b"GIF87a", b"GIF89a")),
            ".webp": lambda data: data[:4] == b"RIFF" and data[8:12] == b"WEBP",
        }
        office_members = {
            ".docx": "word/document.xml",
            ".xlsx": "xl/workbook.xml",
            ".pptx": "ppt/presentation.xml",
        }
        allowed = {*signatures, *office_members, ".txt", ".md", ".csv"}
        if extension not in allowed:
            raise serializers.ValidationError(
                "Allowed formats: PDF, PNG, JPEG, GIF, WebP, DOCX, XLSX, PPTX, MD, TXT and CSV."
            )

        header = upload.read(16)
        upload.seek(0)
        if extension in signatures and not signatures[extension](header):
            raise serializers.ValidationError("The file content does not match its extension.")
        if extension in {".txt", ".md", ".csv"} and b"\x00" in header:
            raise serializers.ValidationError("Text, Markdown and CSV files must not contain binary data.")
        if extension in office_members:
            try:
                with ZipFile(upload) as archive:
                    members = set(archive.namelist())
                    if (
                        "[Content_Types].xml" not in members
                        or office_members[extension] not in members
                    ):
                        raise serializers.ValidationError(
                            "The file content does not match its extension."
                        )
            except (BadZipFile, OSError, EOFError) as error:
                raise serializers.ValidationError("The Office document is damaged or invalid.") from error
            finally:
                upload.seek(0)
        return upload


class GuideListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    cover_image = GuideImageSerializer(read_only=True)
    step_count = serializers.SerializerMethodField()
    has_pdf = serializers.SerializerMethodField()

    class Meta:
        model = Guide
        fields = [
            "slug",
            "title",
            "subtitle",
            "summary",
            "language",
            "guide_type",
            "difficulty",
            "duration_minutes",
            "category",
            "step_count",
            "has_pdf",
            "cover_image",
            "updated_at",
        ]

    def get_step_count(self, obj):
        # Annotated by the list view; falls back to a query elsewhere
        count = getattr(obj, "step_count", None)
        return count if count is not None else obj.steps.count()

    def get_has_pdf(self, obj):
        return obj.attachment.name.lower().endswith(".pdf") if obj.attachment else False


class GuideSerializer(MarkdownHtmlMixin, serializers.ModelSerializer):
    """A guide with all content blocks of its type (see docs/guide-types.md).

    Omitted fields keep their value on update. Block collections that are sent replace the
    stored ones (matched by `id`).
    """

    category = CategorySerializer(read_only=True)
    attachment_info = serializers.SerializerMethodField()
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    guide_type = serializers.ChoiceField(choices=GuideType.choices, required=False)
    summary = serializers.CharField(max_length=300, required=False, allow_blank=True)
    duration_minutes = serializers.IntegerField(
        min_value=1, max_value=1440, required=False, allow_null=True
    )
    # Flat steps: written by free guides; read for every type (search, PDF, simple views)
    steps = StepSerializer(many=True, required=False, max_length=100)
    # The elements a guide is built from, in the order of the guide (type "page")
    elements = ElementSerializer(many=True, required=False, max_length=300)
    images = GuideImageSerializer(many=True, read_only=True)
    cover_image = GuideImageSerializer(read_only=True)
    cover_image_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    change_comment = serializers.CharField(
        write_only=True, required=False, allow_blank=True, max_length=200
    )
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Guide
        fields = [
            "slug",
            "guide_type",
            "title",
            "subtitle",
            "summary",
            "language",
            "difficulty",
            "duration_minutes",
            "category",
            "category_id",
            "steps",
            "elements",
            "images",
            "cover_image",
            "cover_image_id",
            "attachment_info",
            "change_comment",
            "is_locked",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "is_locked", "created_at", "updated_at"]

    def get_attachment_info(self, obj):
        if not obj.attachment:
            return None
        kind = attachment_kind(obj.attachment.name)
        url = f"/api/guides/{obj.slug}/attachment/"
        return {
            "name": PurePosixPath(obj.attachment.name).name,
            "size": obj.attachment.size,
            "download_url": url,
            "kind": kind,
            # The browser shows PDFs and images itself
            "view_url": f"{url}?inline=1" if kind in ("pdf", "image") else None,
            "preview_html": stored_preview_html(obj.attachment) if kind == "html" else "",
        }

    def validate(self, attrs):
        if self.instance is not None:
            guide_type = self.instance.guide_type
            if attrs.get("guide_type", guide_type) != guide_type:
                raise serializers.ValidationError(
                    {"guide_type": "The type of a guide cannot be changed later."}
                )
        else:
            guide_type = attrs.setdefault("guide_type", GuideType.FREE)
        validate_for_type(attrs, guide_type, creating=self.instance is None)
        return attrs

    def _user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    @staticmethod
    def _pop_content(validated_data):
        content = {name: validated_data.pop(name) for name in list(validated_data) if name in ALL_BLOCKS}
        return content.pop("steps", None), content

    @transaction.atomic
    def create(self, validated_data):
        free_steps, content = self._pop_content(validated_data)
        comment = validated_data.pop("change_comment", "")
        cover_image_id = validated_data.pop("cover_image_id", None)
        guide = Guide(**validated_data)
        guide._change_reason = comment or "Guide created"
        guide.save()
        if cover_image_id is not None:
            guide.cover_image = resolve_image(guide, self._user(), cover_image_id, "cover_image_id")
            guide.save(update_fields=["cover_image"])
        if free_steps:
            save_free_steps(guide, free_steps)
        save_blocks(guide, content, self._user())
        return guide

    @transaction.atomic
    def update(self, instance, validated_data):
        free_steps, content = self._pop_content(validated_data)
        comment = validated_data.pop("change_comment", "")
        if "cover_image_id" in validated_data:
            image_id = validated_data.pop("cover_image_id")
            instance.cover_image = resolve_image(instance, self._user(), image_id, "cover_image_id")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance._change_reason = comment or "Guide edited"
        instance.save()
        if free_steps is not None:
            save_free_steps(instance, free_steps)
        save_blocks(instance, content, self._user())
        return instance


def save_free_steps(guide, steps_data):
    """Steps of a free guide: update by id, create new ones, delete the rest."""
    existing = {step.id: step for step in guide.steps.all()}
    keep = set()
    for position, data in enumerate(steps_data, start=1):
        step_id = data.get("id")
        if step_id is not None:
            step = existing.get(step_id)
            if step is None:
                raise serializers.ValidationError(
                    {"steps": f"Step {step_id} does not belong to this guide."}
                )
            step.order = data.get("order", position)
            step.title = data["title"]
            step.body = data["body"]
            step.save()
        else:
            step = Step.objects.create(
                guide=guide,
                order=data.get("order", position),
                title=data["title"],
                body=data["body"],
            )
        keep.add(step.id)
    # Steps that were not sent again are removed
    for step_id, step in existing.items():
        if step_id not in keep:
            step.delete()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            UnicodeUsernameValidator(),
            UniqueValidator(
                queryset=User.objects.all(),
                lookup="iexact",
                message="This user name is already taken.",
            ),
        ],
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    accept_terms = serializers.BooleanField()
    # Honeypot: invisible to people, bots often fill it in
    website = serializers.CharField(required=False, allow_blank=True, default="")
    captcha_token = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_accept_terms(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "Please accept the terms of use and the privacy policy."
            )
        return value

    def validate(self, attrs):
        try:
            validate_password(attrs["password"], User(username=attrs["username"], email=attrs["email"]))
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)})
        return attrs


class MarkdownRenderSerializer(serializers.Serializer):
    """Texts to render for the live preview. Limits keep one request cheap."""

    texts = serializers.ListField(
        child=serializers.CharField(max_length=5000, allow_blank=True, trim_whitespace=False),
        min_length=1,
        max_length=100,
    )

    def validate_texts(self, texts):
        if sum(len(text) for text in texts) > 100_000:
            raise serializers.ValidationError("Too much text at once.")
        return texts


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class UidTokenSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class PasswordResetConfirmSerializer(UidTokenSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(trim_whitespace=False)


class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["reason", "comment"]


class ReportSerializer(serializers.ModelSerializer):
    guide = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    guide_title = serializers.CharField(source="guide.title", read_only=True)
    guide_locked = serializers.BooleanField(source="guide.is_locked", read_only=True)
    reporter = serializers.CharField(source="reporter.username", read_only=True, default=None)
    resolved_by = serializers.CharField(source="resolved_by.username", read_only=True, default=None)
    reason_label = serializers.CharField(source="get_reason_display", read_only=True)
    reported_comment = serializers.IntegerField(source="reported_comment_id", read_only=True)
    reported_comment_body = serializers.CharField(source="reported_comment.body", read_only=True, default=None)

    class Meta:
        model = Report
        fields = [
            "id", "guide", "guide_title", "guide_locked", "reporter", "reason", "reason_label",
            "comment", "reported_comment", "reported_comment_body", "created_at", "resolved_at",
            "resolved_by", "resolution_note",
        ]


class ResolveSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")


def user_payload(user):
    """Details about the signed-in user for the frontend."""
    hint = write_denial(user)
    return {
        "username": user.get_username(),
        "email": user.email,
        "is_moderator": is_moderator(user),
        "can_write": hint is None,
        "write_hint": hint or "",
    }
