from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from difflib import get_close_matches

from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password as get_password_hash

from ..attachments import INLINE_TYPES, attachment_kind, build_preview_html, extension
from ..auth import issue_tokens, revoke_refresh_token, revoke_user_tokens
from ..captcha import verify_captcha
from ..mails import (
    send_already_registered_mail,
    send_password_reset_mail,
    send_verification_mail,
)
from ..models import (
    Category,
    Guide,
    GuideComment,
    GuideImage,
    GuideStatus,
    Profile,
    Report,
    CommentVote,
    GuideElement,
    Step,
)
from ..permissions import CanDelete, CanWrite, IsModerator, is_moderator
from ..templatetags.guide_extras import render_markdown
from ..tokens import decode_uid, email_verification_token
from ..elements import anchor_label
from ..views import _search
from .content import GuideImageSerializer, GuideImageUploadSerializer
from .serializers import (
    CategorySerializer,
    EmailSerializer,
    GuideAttachmentUploadSerializer,
    GuideCommentPreviewSerializer,
    GuideCommentSerializer,
    GuideListSerializer,
    GuideSerializer,
    HideCommentSerializer,
    LoginSerializer,
    MarkdownRenderSerializer,
    PasswordResetConfirmSerializer,
    PasswordSerializer,
    RefreshSerializer,
    RegisterSerializer,
    ReportCreateSerializer,
    ReportSerializer,
    ResolveSerializer,
    UidTokenSerializer,
    user_payload,
)

HISTORY_TYPES = {"+": "created", "~": "changed", "-": "deleted"}

REGISTER_MESSAGE = (
    "Almost done! If the details are correct, we have sent you an e-mail with a "
    "confirmation link. Your account becomes active once you confirm it."
)
MAIL_MESSAGE = "If the details match an account, we have sent you an e-mail."
INVALID_LINK = (
    "The link is invalid, has expired or was already used. "
    "If you have already confirmed your account, just sign in."
)


def client_ip(request):
    return BaseThrottle().get_ident(request)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    pagination_class = None


class GuideViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Read guides (public), create, edit and delete them (account rules), report and lock them."""

    lookup_field = "slug"
    http_method_names = ["get", "post", "put", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in (
            "create", "update", "preview_create", "preview_update", "attachment_preview"
        ):
            return [IsAuthenticated(), CanWrite()]
        if self.action in ("destroy", "archive", "restore"):
            return [IsAuthenticated(), CanDelete()]
        if self.action in ("mark_outdated", "mark_current"):
            return [IsAuthenticated(), CanWrite()]
        if self.action in ("comment_hide", "lock", "unlock"):
            return [IsModerator()]
        if self.action == "report":
            return [IsAuthenticated()]
        if self.action in ("edit_comment", "comment_preview", "comment_helpful", "comment_answer", "comment_report"):
            return [IsAuthenticated()]
        if self.action == "attachment" and self.request.method in ("POST", "DELETE"):
            return [IsAuthenticated(), CanWrite()]
        if self.action == "comments" and self.request.method == "POST":
            return [IsAuthenticated()]
        return [IsAuthenticatedOrReadOnly()]

    def get_throttles(self):
        # Reading is unlimited; writing and reporting are rate limited
        if self.action in (
            "create", "update", "destroy", "preview_create", "preview_update", "attachment_preview",
            "archive", "restore", "mark_outdated", "mark_current",
        ):
            self.throttle_scope = "write"
        elif self.action == "report":
            self.throttle_scope = "report"
        elif self.action == "comments" and self.request.method == "POST":
            self.throttle_scope = "comment"
        elif self.action in ("edit_comment", "comment_preview", "comment_helpful", "comment_answer"):
            self.throttle_scope = "comment"
        elif self.action == "comment_report":
            self.throttle_scope = "report"
        elif self.action == "attachment" and self.request.method in ("POST", "DELETE"):
            self.throttle_scope = "write"
        else:
            return []
        return [ScopedRateThrottle()]

    def get_queryset(self):
        queryset = Guide.objects.select_related("category", "created_by")
        if self.action == "list":
            return self._filter_list(queryset)
        return queryset.prefetch_related(
            "steps",
            "images",
            "cover_image",
            Prefetch("elements", queryset=GuideElement.objects.select_related("image")),
        )

    def _filter_list(self, queryset):
        """Overview filters: ?category=, ?type=, ?difficulty=, ?language=, ?max_duration=, ?has_pdf=1, ?q="""
        params = self.request.query_params
        if params.get("category"):
            queryset = queryset.filter(category__slug=params["category"])
        if params.get("type"):
            queryset = queryset.filter(guide_type=params["type"])
        if params.get("difficulty"):
            queryset = queryset.filter(difficulty=params["difficulty"])
        if params.get("language"):
            queryset = queryset.filter(language=params["language"])
        if params.get("max_duration", "").isdigit():
            queryset = queryset.filter(duration_minutes__lte=int(params["max_duration"]))
        if params.get("has_pdf") == "1":
            queryset = queryset.filter(attachment__iendswith=".pdf")
        queryset = _search(queryset.exclude(status=GuideStatus.ARCHIVED), params.get("q"))
        return self._with_step_count(queryset)

    @staticmethod
    def _with_step_count(queryset):
        return queryset.annotate(
            step_count=Count("steps", distinct=True)
            + Count("elements", filter=Q(elements__kind="step"), distinct=True)
        )

    def get_serializer_class(self):
        return GuideListSerializer if self.action == "list" else GuideSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, guide):
        """Delete the guide with all its blocks; its files are removed after the commit.

        The history records stay in the database, so an admin can restore a guide.
        """
        files = [guide.attachment] if guide.attachment else []
        files += [image.file for image in guide.images.all() if image.file]
        names = [(file.storage, file.name) for file in files]
        guide._change_reason = "Guide deleted"
        guide.delete()
        transaction.on_commit(lambda: [storage.delete(name) for storage, name in names])

    def _preview(self, request, guide=None):
        """Show the guide as it would look after saving, without keeping anything.

        The changes are written inside a savepoint, serialized and rolled back, so the
        preview uses exactly the same validation and rendering as a real save.
        """
        context = self.get_serializer_context()
        serializer = GuideSerializer(guide, data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            savepoint = transaction.savepoint()
            try:
                extra = {} if guide is not None else {"created_by": request.user}
                saved = serializer.save(**extra)
                # Reload: prefetched blocks of the old state may have been deleted meanwhile
                fresh = self.get_queryset().get(pk=saved.pk)
                data = GuideSerializer(fresh, context=context).data
            finally:
                transaction.savepoint_rollback(savepoint)
        return Response(data)

    @action(detail=False, methods=["post"], url_path="preview")
    def preview_create(self, request):
        return self._preview(request)

    @action(detail=True, methods=["post"], url_path="preview")
    def preview_update(self, request, slug=None):
        return self._preview(request, self.get_object())

    @action(detail=True, methods=["get"])
    def history(self, request, slug=None):
        guide = self.get_object()
        guide_changes = [
            {
                "date": h.history_date,
                "user": h.history_user.get_username() if h.history_user else None,
                "type": HISTORY_TYPES[h.history_type],
                "reason": h.history_change_reason or "",
                "title": h.title,
                "attachment": h.attachment.rsplit("/", 1)[-1] if h.attachment else None,
            }
            for h in guide.history.select_related("history_user")
        ]
        step_changes = [
            {
                "date": h.history_date,
                "user": h.history_user.get_username() if h.history_user else None,
                "type": HISTORY_TYPES[h.history_type],
                "order": h.order,
                "title": h.title,
            }
            for h in Step.history.filter(guide_id=guide.pk)
            .select_related("history_user")
            .order_by("-history_date")
        ]
        return Response({"guide": guide_changes, "steps": step_changes})

    @action(detail=True, methods=["post"])
    def report(self, request, slug=None):
        guide = self.get_object()
        if Report.objects.filter(guide=guide, reporter=request.user, resolved_at=None).exists():
            return Response({"detail": "You have already reported this guide. Thank you!"})
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(guide=guide, reporter=request.user)
        return Response(
            {"detail": "Thanks for your report. A moderator will take a look at the guide."},
            status=status.HTTP_201_CREATED,
        )

    def _comments(self, guide):
        return guide.comments.select_related("author", "guide", "parent").prefetch_related("votes")

    def _comment(self, guide, comment_id):
        return get_object_or_404(self._comments(guide), pk=comment_id)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, slug=None):
        guide = self.get_object()
        if request.method == "GET":
            return Response(
                GuideCommentSerializer(self._comments(guide), many=True, context={"request": request}).data
            )

        serializer = GuideCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        extra = {"guide": guide, "author": request.user}
        parent_id, element_id = data.get("parent_id"), data.get("element_id")
        if parent_id is not None:
            parent = get_object_or_404(GuideComment, guide=guide, pk=parent_id)
            if parent.parent_id is not None:
                raise ValidationError({"parent_id": "Reply to the comment at the top of the thread."})
            # a reply is always a plain comment about the same place
            extra.update(parent=parent, element=parent.element, anchor=parent.anchor, kind=GuideComment.Kind.COMMENT)
        elif element_id is not None:
            element = get_object_or_404(GuideElement, guide=guide, pk=element_id)
            extra.update(element=element, anchor=anchor_label(element))
        comment = serializer.save(**extra)
        comment = self._comment(guide, comment.pk)
        return Response(
            GuideCommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="comments/preview")
    def comment_preview(self, request, slug=None):
        serializer = GuideCommentPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            "body_html": str(render_markdown(serializer.validated_data["body"]))
        })

    @action(
        detail=True,
        methods=["put"],
        url_path=r"comments/(?P<comment_id>[0-9]+)",
    )
    def edit_comment(self, request, slug=None, comment_id=None):
        guide = self.get_object()
        comment = get_object_or_404(
            GuideComment.objects.select_related("author"),
            guide=guide,
            pk=comment_id,
        )
        if comment.author_id != request.user.pk and not is_moderator(request.user):
            raise PermissionDenied("You can only edit your own comments.")
        if comment.hidden_at is not None and not is_moderator(request.user):
            raise PermissionDenied("A moderator hid this comment, so it cannot be edited.")

        serializer = GuideCommentSerializer(comment, data=request.data)
        serializer.is_valid(raise_exception=True)
        comment.body = serializer.validated_data["body"]
        comment.edited_at = timezone.now()
        comment._change_reason = "Comment edited"
        comment.save()
        return Response(
            GuideCommentSerializer(comment, context={"request": request}).data
        )

    @action(detail=True, methods=["post", "delete"], url_path=r"comments/(?P<comment_id>[0-9]+)/helpful")
    def comment_helpful(self, request, slug=None, comment_id=None):
        """"Helpful" for a comment: once per user, never for one's own comment."""
        guide = self.get_object()
        comment = self._comment(guide, comment_id)
        if request.method == "POST":
            if comment.author_id == request.user.pk:
                raise ValidationError({"detail": "You cannot mark your own comment as helpful."})
            CommentVote.objects.get_or_create(comment=comment, user=request.user)
        else:
            CommentVote.objects.filter(comment=comment, user=request.user).delete()
        comment = self._comment(guide, comment_id)
        return Response(GuideCommentSerializer(comment, context={"request": request}).data)

    @action(detail=True, methods=["post", "delete"], url_path=r"comments/(?P<comment_id>[0-9]+)/answer")
    def comment_answer(self, request, slug=None, comment_id=None):
        """Mark a reply to a question as its answer (one answer per question)."""
        guide = self.get_object()
        comment = self._comment(guide, comment_id)
        if not GuideCommentSerializer(comment, context={"request": request}).data["can_mark_answer"]:
            raise PermissionDenied("Only the asker, the author of the guide and moderators can mark an answer.")
        if request.method == "POST":
            GuideComment.objects.filter(parent=comment.parent).exclude(pk=comment.pk).update(is_answer=False)
        comment.is_answer = request.method == "POST"
        comment._change_reason = "Answer marked" if comment.is_answer else "Answer unmarked"
        comment.save()
        comment = self._comment(guide, comment_id)
        return Response(GuideCommentSerializer(comment, context={"request": request}).data)

    @action(detail=True, methods=["post", "delete"], url_path=r"comments/(?P<comment_id>[0-9]+)/hide")
    def comment_hide(self, request, slug=None, comment_id=None):
        """Moderators hide a comment with a reason (POST) or show it again (DELETE)."""
        guide = self.get_object()
        comment = self._comment(guide, comment_id)
        if request.method == "POST":
            serializer = HideCommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            comment.hidden_at = timezone.now()
            comment.hidden_by = request.user
            comment.hidden_reason = serializer.validated_data["reason"]
            comment._change_reason = "Comment hidden"
        else:
            comment.hidden_at, comment.hidden_by, comment.hidden_reason = None, None, ""
            comment._change_reason = "Comment shown again"
        comment.save()
        comment = self._comment(guide, comment_id)
        return Response(GuideCommentSerializer(comment, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path=r"comments/(?P<comment_id>[0-9]+)/report")
    def comment_report(self, request, slug=None, comment_id=None):
        guide = self.get_object()
        comment = self._comment(guide, comment_id)
        if Report.objects.filter(reported_comment=comment, reporter=request.user, resolved_at=None).exists():
            return Response({"detail": "You have already reported this comment. Thank you!"})
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(guide=guide, reporter=request.user, reported_comment=comment)
        return Response(
            {"detail": "Thanks for your report. A moderator will take a look at the comment."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="attachment-preview")
    def attachment_preview(self, request):
        """Preview a file before publishing (nothing is stored)."""
        serializer = GuideAttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]
        kind = attachment_kind(upload.name)
        return Response({
            "kind": kind,
            "preview_html": build_preview_html(upload, upload.name) if kind == "html" else "",
        })

    @action(detail=True, methods=["get", "post", "delete"])
    def attachment(self, request, slug=None):
        guide = self.get_object()
        if request.method == "GET":
            if not guide.attachment:
                raise NotFound("This guide has no attachment.")
            filename = guide.attachment.name.rsplit("/", 1)[-1]
            # ?inline=1: PDFs and images for display on the guide page (only these types,
            # with their real content type). Everything else is always served as a download.
            inline_type = INLINE_TYPES.get(extension(filename))
            inline = request.query_params.get("inline") == "1" and inline_type is not None
            response = FileResponse(
                guide.attachment.open("rb"),
                as_attachment=not inline,
                filename=filename,
                content_type=inline_type if inline else "application/octet-stream",
            )
            response["X-Content-Type-Options"] = "nosniff"
            if inline:
                response["X-Frame-Options"] = "SAMEORIGIN"  # embedding on our own pages
                if inline_type.startswith("image/"):
                    response["Content-Security-Policy"] = "default-src 'none'; sandbox"
            return response

        if request.method == "POST":
            serializer = GuideAttachmentUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            old_name = guide.attachment.name
            old_storage = guide.attachment.storage
            upload = serializer.validated_data["file"]
            guide.attachment.save(upload.name, upload, save=False)
            guide._change_reason = "Guide attachment uploaded"
            guide.save(update_fields=["attachment", "updated_at"])
            if old_name:
                transaction.on_commit(lambda: old_storage.delete(old_name))
            return Response(GuideSerializer(guide).data)

        old_name = guide.attachment.name
        if old_name:
            storage = guide.attachment.storage
            guide.attachment = ""
            guide._change_reason = "Guide attachment removed"
            guide.save(update_fields=["attachment", "updated_at"])
            transaction.on_commit(lambda: storage.delete(old_name))
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _set_locked(self, request, locked):
        guide = self.get_object()
        if guide.is_locked != locked:
            guide.is_locked = locked
            guide._change_reason = "Guide locked" if locked else "Guide unlocked"
            guide.save()
        return Response({"is_locked": guide.is_locked})

    @action(detail=True, methods=["post"])
    def lock(self, request, slug=None):
        return self._set_locked(request, True)

    @action(detail=True, methods=["post"])
    def unlock(self, request, slug=None):
        return self._set_locked(request, False)

    def _set_status(self, new_status, reason, allowed_from):
        """Move a guide to a new status; asking for the status it has is not an error."""
        guide = self.get_object()
        if guide.status != new_status:
            if guide.status not in allowed_from:
                raise ValidationError({"detail": f"A guide that is {guide.get_status_display().lower()} cannot do this."})
            guide.status = new_status
            guide._change_reason = reason
            guide.save(update_fields=["status"])  # a status change is not an edit: updated_at stays
        return Response({"status": guide.status})

    @action(detail=True, methods=["post"])
    def archive(self, request, slug=None):
        """Take a guide out of search and overview without deleting it (author and moderators)."""
        return self._set_status(
            GuideStatus.ARCHIVED, "Guide archived", {GuideStatus.PUBLISHED, GuideStatus.OUTDATED}
        )

    @action(detail=True, methods=["post"])
    def restore(self, request, slug=None):
        return self._set_status(GuideStatus.PUBLISHED, "Guide restored", {GuideStatus.ARCHIVED})

    @action(detail=True, methods=["post"], url_path="mark-outdated")
    def mark_outdated(self, request, slug=None):
        """Show readers that steps may no longer work (anyone who may edit the guide)."""
        return self._set_status(GuideStatus.OUTDATED, "Guide marked as outdated", {GuideStatus.PUBLISHED})

    @action(detail=True, methods=["post"], url_path="mark-current")
    def mark_current(self, request, slug=None):
        return self._set_status(GuideStatus.PUBLISHED, "Guide marked as up to date", {GuideStatus.OUTDATED})

    @action(detail=True, methods=["get"])
    def related(self, request, slug=None):
        """Up to three other guides of the same category, newest first."""
        guide = self.get_object()
        if guide.category_id is None:
            return Response([])
        others = (
            Guide.objects.select_related("category")
            .filter(category_id=guide.category_id)
            .exclude(pk=guide.pk)
            .exclude(status=GuideStatus.ARCHIVED)
        )
        related = self._with_step_count(others).order_by("-updated_at")[:3]
        return Response(GuideListSerializer(related, many=True, context={"request": request}).data)

    @action(detail=False, methods=["get"])
    def suggest(self, request):
        """Suggestions while typing in the search: guides and categories, or the closest title."""
        query = (request.query_params.get("q") or "").strip()[:80]
        if len(query) < 2:
            return Response({"guides": [], "categories": [], "did_you_mean": ""})
        visible = Guide.objects.exclude(status=GuideStatus.ARCHIVED)
        guides = [
            {"slug": slug, "title": title}
            for slug, title in visible.filter(title__icontains=query).values_list("slug", "title")[:5]
        ]
        categories = [
            {"slug": slug, "name": name}
            for slug, name in Category.objects.filter(name__icontains=query).values_list("slug", "name")[:2]
        ]
        did_you_mean = ""
        if not guides and not categories:
            titles = {title.lower(): title for title in visible.values_list("title", flat=True)}
            close = get_close_matches(query.lower(), titles, n=1, cutoff=0.6)
            did_you_mean = titles[close[0]] if close else ""
        return Response({"guides": guides, "categories": categories, "did_you_mean": did_you_mean})


class GuideImageViewSet(viewsets.GenericViewSet):
    """Images for guide content: upload (POST /api/images/) and show (GET /api/images/<id>/).

    An uploaded image belongs to nobody's guide until a saved guide references it; until then
    only the uploader can see or use it.
    """

    queryset = GuideImage.objects.select_related("guide")

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), CanWrite()]
        return [AllowAny()]

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "write"
            return [ScopedRateThrottle()]
        return []

    def create(self, request):
        serializer = GuideImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        image = GuideImage(
            alt=data["alt"], caption=data["caption"].strip(), kind=data["kind"], uploaded_by=request.user
        )
        upload = serializer.validated_data["file"]
        image.file.save(upload.name, upload, save=False)
        image.save()
        return Response(GuideImageSerializer(image).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        image = self.get_object()
        if image.guide_id is None and image.uploaded_by_id != getattr(request.user, "pk", None):
            raise NotFound()
        content_type = INLINE_TYPES.get(extension(image.file.name), "application/octet-stream")
        response = FileResponse(image.file.open("rb"), content_type=content_type)
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Security-Policy"] = "default-src 'none'; sandbox"
        response["Cache-Control"] = "public, max-age=86400"
        return response


class ReportViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Reports for moderators: ?status=open (default), resolved or all."""

    serializer_class = ReportSerializer
    permission_classes = [IsModerator]

    def get_queryset(self):
        queryset = Report.objects.select_related("guide", "reporter", "resolved_by")
        wanted = self.request.query_params.get("status", "open")
        if wanted == "open":
            return queryset.filter(resolved_at=None)
        if wanted == "resolved":
            return queryset.exclude(resolved_at=None)
        return queryset

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        report = self.get_object()
        serializer = ResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if report.resolved_at is None:
            report.resolved_at = timezone.now()
            report.resolved_by = request.user
            report.resolution_note = serializer.validated_data["note"]
            report.save()
        return Response(ReportSerializer(report).data)


# Accounts
class PublicAuthView(APIView):
    """Base for endpoints without login (a stale token is ignored)."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RegisterView(PublicAuthView):
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        generic = Response({"detail": REGISTER_MESSAGE}, status=status.HTTP_201_CREATED)

        if data["website"]:  # Honeypot filled in: a bot. Pretend success, create nothing.
            return generic
        if not verify_captcha(data["captcha_token"], client_ip(request)):
            return Response(
                {"captcha_token": ["Please solve the captcha and try again."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = User.objects.normalize_email(data["email"].strip())
        if User.objects.filter(email__iexact=email).exists():
            # Do not reveal that the address exists: same answer as otherwise
            send_already_registered_mail(email)
            return generic

        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"],
                email=email,
                password=data["password"],
                is_active=False,  # active only after confirming the e-mail address
            )
            Profile.objects.create(user=user, terms_accepted_at=timezone.now())
        send_verification_mail(user)
        return generic


class VerifyEmailView(PublicAuthView):
    def post(self, request):
        serializer = UidTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(pk=decode_uid(serializer.validated_data["uid"])).first()
        if user is None or not email_verification_token.check_token(
            user, serializer.validated_data["token"]
        ):
            return Response({"detail": INVALID_LINK}, status=status.HTTP_400_BAD_REQUEST)
        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.banned:
            return Response(
                {"detail": "Your account is banned."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
            profile.email_verified_at = timezone.now()
            profile.save(update_fields=["email_verified_at"])
        return Response({"detail": "Your e-mail address is confirmed. You can sign in now."})


class ResendVerificationView(PublicAuthView):
    throttle_scope = "mail"

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = (
            User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=False)
            .select_related("profile")
            .first()
        )
        profile = getattr(user, "profile", None)
        if user and profile and not profile.banned and profile.email_verified_at is None:
            send_verification_mail(user)
        return Response({"detail": MAIL_MESSAGE})


class LoginView(PublicAuthView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request=request, username=username, password=password)
        if user is None:
            candidate = User.objects.filter(username=username).select_related("profile").first()
            if candidate and not candidate.is_active and candidate.check_password(password):
                profile = getattr(candidate, "profile", None)
                if profile and profile.banned:
                    return Response(
                        {"detail": "Your account is banned.", "code": "banned"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                return Response(
                    {
                        "detail": "Please confirm your e-mail address first.",
                        "code": "email_not_verified",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"detail": "User name or password is wrong."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({**issue_tokens(user), "user": user_payload(user)})


class RefreshView(PublicAuthView):
    """Exchange a refresh token for a new token pair (rotation)."""

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            old = RefreshToken(serializer.validated_data["refresh"])
            user = User.objects.filter(pk=old["user_id"], is_active=True).first()
            # A password change invalidates old tokens here, too
            if user is None or old.get("hash_password") != get_password_hash(user.password):
                raise TokenError("Account no longer valid")
            old.blacklist()
        except (TokenError, KeyError):
            return Response(
                {"detail": "Please sign in again.", "code": "token_invalid"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({**issue_tokens(user), "user": user_payload(user)})


class MarkdownRenderView(APIView):
    """Render Markdown for the live preview in the editor: no database access at all.

    Uses the same renderer and sanitizer as saved guides, so the preview matches the
    published page. Only for signed-in users, with its own generous rate limit.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "preview"

    def post(self, request):
        serializer = MarkdownRenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"html": [str(render_markdown(text)) for text in serializer.validated_data["texts"]]})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(user_payload(request.user))


class LogoutView(PublicAuthView):
    """Revoke the refresh token (the access token expires by itself)."""

    def post(self, request):
        refresh = request.data.get("refresh") if hasattr(request.data, "get") else None
        if refresh:
            revoke_refresh_token(refresh)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(PublicAuthView):
    throttle_scope = "mail"

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"], is_active=True
        ).first()
        if user and user.has_usable_password():
            send_password_reset_mail(user)
        return Response({"detail": MAIL_MESSAGE})


class PasswordResetConfirmView(PublicAuthView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.filter(pk=decode_uid(data["uid"]), is_active=True).first()
        if user is None or not default_token_generator.check_token(user, data["token"]):
            return Response(
                {"detail": "The link is invalid or has expired. Request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(data["password"], user)
        except DjangoValidationError as error:
            return Response({"password": list(error.messages)}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data["password"])
        user.save(update_fields=["password"])
        revoke_user_tokens(user)  # sign out everywhere
        return Response({"detail": "Your password has been changed. You can sign in now."})


class AccountView(APIView):
    """DELETE: delete your own account (with password). Contributions stay, without a name."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def delete(self, request):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["password"]):
            return Response(
                {"password": ["The password is wrong."]}, status=status.HTTP_400_BAD_REQUEST
            )
        if user.is_staff or user.is_superuser:
            return Response(
                {"detail": "Please delete administrator accounts in the admin area."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
