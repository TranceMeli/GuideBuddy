from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from simple_history.models import HistoricalRecords

RESERVED_SLUGS = {"neu", "new", "preview", "attachment-preview"}  # would collide with API URLs


def unique_slug(model, value, instance=None):
    """Build a unique slug (title, title-2, title-3, ...)."""
    base = slugify(value)[:80] or "guide"
    slug, counter = base, 2
    while (
        slug in RESERVED_SLUGS
        or model.objects.filter(slug=slug).exclude(pk=getattr(instance, "pk", None)).exists()
    ):
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class Category(models.Model):
    name = models.CharField("Name", max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Category, self.name, self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("guides:category", args=[self.slug])


class GuideType(models.TextChoices):
    """A guide is built from elements (`page`); `free` is a finished text or an uploaded file."""

    PAGE = "page", "Guide"
    FREE = "free", "File or text"


class Difficulty(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"


# Languages a guide can be written in (BCP 47 tag). GuideBuddy is English only for now;
# the field stays so the lang attribute of the reading view, PDF and EPUB keeps a source
# and more languages can be added later without changing the API.
GUIDE_LANGUAGES = [
    ("en", "English"),
]


class Guide(models.Model):
    title = models.CharField("Title", max_length=160)
    subtitle = models.CharField("Subtitle", max_length=200, blank=True)
    language = models.CharField("Language", max_length=10, choices=GUIDE_LANGUAGES, default="en")
    # Fixed at creation: the content blocks of one type do not fit another
    guide_type = models.CharField(
        "Guide type", max_length=20, choices=GuideType.choices, default=GuideType.FREE
    )
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        verbose_name="Category",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="guides",
    )
    summary = models.TextField("Summary", blank=True)
    difficulty = models.CharField("Level", max_length=20, choices=Difficulty.choices, blank=True)
    duration_minutes = models.PositiveSmallIntegerField("Duration (minutes)", null=True, blank=True)
    # Preview image on the overview cards (an uploaded GuideImage)
    cover_image = models.ForeignKey(
        "GuideImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    attachment = models.FileField("Attachment", upload_to="guide-attachments/%Y/%m/", blank=True)
    is_locked = models.BooleanField(
        "Locked",
        default=False,
        help_text="Only moderators may edit locked guides.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="guides",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Guide"
        verbose_name_plural = "Guides"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Guide, self.title, self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("guides:detail", args=[self.slug])


class Ordered(models.Model):
    """Base for content blocks that belong to a guide and keep a manual order."""

    order = models.PositiveIntegerField("No.", default=1)

    class Meta:
        abstract = True
        ordering = ["order", "id"]


class ImageKind(models.TextChoices):
    """What an image is. Readers see it in the caption, so a drawn interface is never
    passed off as a real screenshot."""

    PHOTO = "photo", "Photo"
    SCREENSHOT = "screenshot", "Screenshot"
    MOCKUP = "mockup", "Mockup (schematic)"
    DIAGRAM = "diagram", "Diagram"


class GuideImage(models.Model):
    """An image referenced by id from content blocks.

    Uploaded before the guide is saved (so new guides can have images, too); `guide` is set
    when a saved guide first references it. Until then only the uploader may use it.
    """

    guide = models.ForeignKey(
        Guide, null=True, blank=True, on_delete=models.CASCADE, related_name="images"
    )
    file = models.ImageField(
        "Image", upload_to="guide-images/%Y/%m/", width_field="width", height_field="height"
    )
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    alt = models.CharField("Alt text", max_length=200)
    caption = models.CharField("Caption", max_length=200, blank=True)
    kind = models.CharField("Kind", max_length=12, choices=ImageKind.choices, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Image"
        verbose_name_plural = "Images"

    def __str__(self):
        return self.alt


class Step(models.Model):
    """One step of a free guide (title and text). Guides built from elements use GuideElement."""

    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveIntegerField("No.", default=1)
    title = models.CharField("Title", max_length=160)
    body = models.TextField("Content (Markdown)")

    history = HistoricalRecords()

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Step"
        verbose_name_plural = "Steps"

    def __str__(self):
        return f"{self.order}. {self.title}"


class ElementKind(models.TextChoices):
    """What an element of a guide is. The tools of the guide builder create these."""

    SECTION = "section", "Section"
    STEP = "step", "Step"
    HEADING = "heading", "Heading"
    DIVIDER = "divider", "Divider"
    TEXT = "text", "Text"
    LIST = "list", "List"
    CHECKLIST = "checklist", "Checklist"
    QUOTE = "quote", "Quote"
    LINK = "link", "Link"
    TABLE = "table", "Table"
    COLLAPSIBLE = "collapsible", "Collapsible"
    IMPORTANT = "important", "Important"
    WARNING = "warning", "Warning"
    DANGER = "danger", "Danger"
    ERROR = "error", "Error"
    TIP = "tip", "Tip"
    NOTE = "note", "Note"
    RESULT = "result", "Expected result"
    IMAGE = "image", "Image"
    DIAGRAM = "diagram", "Diagram"
    TERMINAL = "terminal", "Terminal"
    CODE = "code", "Code"
    COMPARE = "compare", "Wrong and right"
    DOWNLOAD = "download", "Download"


class GuideElement(Ordered):
    """One element of a guide, in any order. `text` is the main text (the title of a section or
    step, the Markdown of a text or notice, the caption of an image); `data` holds what the
    kind needs besides (see guides/api/elements.py)."""

    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name="elements")
    kind = models.CharField("Kind", max_length=20, choices=ElementKind.choices)
    text = models.TextField("Text", blank=True)
    data = models.JSONField("Data", default=dict, blank=True)
    image = models.ForeignKey(
        GuideImage, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    history = HistoricalRecords()

    class Meta(Ordered.Meta):
        verbose_name = "Element"
        verbose_name_plural = "Elements"

    def __str__(self):
        return f"{self.kind}: {self.text[:40]}"


class GuideComment(models.Model):
    """A comment on a guide, on one of its elements, or a reply to another comment (one level)."""

    class Kind(models.TextChoices):
        COMMENT = "comment", "Comment"
        QUESTION = "question", "Question"

    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name="comments")
    kind = models.CharField("Kind", max_length=10, choices=Kind.choices, default=Kind.COMMENT)
    # The element the comment is about; "anchor" keeps its name if the element is deleted later
    element = models.ForeignKey(
        GuideElement, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    anchor = models.CharField("About", max_length=120, blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    # A reply to a question that answered it
    is_answer = models.BooleanField("Answer", default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="guide_comments",
    )
    body = models.TextField("Comment", max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"Comment on {self.guide}"


class CommentVote(models.Model):
    """"Helpful" for a comment, once per signed-in user."""

    comment = models.ForeignKey(GuideComment, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["comment", "user"], name="one_vote_per_user_and_comment")]

    def __str__(self):
        return f"{self.user} found comment {self.comment_id} helpful"


class Profile(models.Model):
    """Extra account data: e-mail confirmation, consent, ban."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    email_verified_at = models.DateTimeField("E-mail confirmed at", null=True, blank=True)
    terms_accepted_at = models.DateTimeField("Terms accepted at", null=True, blank=True)
    banned_at = models.DateTimeField("Banned at", null=True, blank=True)
    ban_reason = models.CharField("Ban reason", max_length=200, blank=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    @property
    def banned(self):
        return self.banned_at is not None

    def __str__(self):
        return f"Profile of {self.user}"


class Report(models.Model):
    """A report about a guide by a signed-in user."""

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam or advertising"
        VANDALISM = "vandalism", "Vandalism or false content"
        COPYRIGHT = "copyright", "Copyright infringement"
        ILLEGAL = "illegal", "Illegal content"
        OTHER = "other", "Other"

    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name="reports")
    # Set when a single comment is reported instead of the whole guide
    reported_comment = models.ForeignKey(
        GuideComment, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports"
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports",
    )
    reason = models.CharField("Reason", max_length=20, choices=Reason.choices)
    comment = models.TextField("Remark", blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_reports",
    )
    resolution_note = models.CharField("Resolution note", max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Report"
        verbose_name_plural = "Reports"

    @property
    def is_open(self):
        return self.resolved_at is None

    def __str__(self):
        return f"{self.get_reason_display()} – {self.guide}"
