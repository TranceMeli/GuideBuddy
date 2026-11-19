from django.contrib import admin
from django.utils import timezone
from simple_history.admin import SimpleHistoryAdmin

from .auth import revoke_user_tokens
from .models import (
    Category,
    Guide,
    GuideElement,
    GuideComment,
    GuideImage,
    Profile,
    Report,
    Step,
)


class StepInline(admin.StackedInline):
    model = Step
    extra = 0
    fields = ("order", "title", "body")


class ElementInline(admin.StackedInline):
    model = GuideElement
    extra = 0
    fields = ("order", "kind", "text", "data", "image")


@admin.register(Guide)
class GuideAdmin(SimpleHistoryAdmin):
    list_display = ("title", "guide_type", "category", "status", "is_locked", "created_by", "updated_at")
    list_filter = ("guide_type", "status", "category", "difficulty", "is_locked")
    search_fields = ("title", "subtitle", "summary")
    inlines = [ElementInline, StepInline]
    actions = ["lock_guides", "unlock_guides"]

    @admin.action(description="Lock selected guides")
    def lock_guides(self, request, queryset):
        queryset.update(is_locked=True)

    @admin.action(description="Unlock selected guides")
    def unlock_guides(self, request, queryset):
        queryset.update(is_locked=False)


@admin.register(GuideImage)
class GuideImageAdmin(admin.ModelAdmin):
    list_display = ("alt", "guide", "uploaded_by", "created_at")
    readonly_fields = ("width", "height", "created_at")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")


@admin.register(GuideComment)
class GuideCommentAdmin(SimpleHistoryAdmin):
    list_display = ("guide", "author", "created_at")
    list_filter = ("created_at",)
    search_fields = ("guide__title", "author__username", "body")
    readonly_fields = ("created_at",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "email_verified_at", "terms_accepted_at", "banned_at")
    list_filter = ("banned_at",)
    search_fields = ("user__username", "user__email")
    actions = ["ban_users", "unban_users"]

    @admin.display(description="E-Mail")
    def email(self, obj):
        return obj.user.email

    @admin.action(description="Ban accounts (they can no longer sign in)")
    def ban_users(self, request, queryset):
        for profile in queryset.select_related("user"):
            if profile.user.is_superuser:
                continue  # never lock out admins by accident
            profile.banned_at = timezone.now()
            profile.save(update_fields=["banned_at"])
            profile.user.is_active = False
            profile.user.save(update_fields=["is_active"])
            revoke_user_tokens(profile.user)

    @admin.action(description="Lift the ban")
    def unban_users(self, request, queryset):
        for profile in queryset.select_related("user"):
            profile.banned_at = None
            profile.ban_reason = ""
            profile.save(update_fields=["banned_at", "ban_reason"])
            # Only reactivate accounts with a confirmed e-mail address
            if profile.email_verified_at:
                profile.user.is_active = True
                profile.user.save(update_fields=["is_active"])


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("guide", "reason", "reporter", "created_at", "resolved_at")
    list_filter = ("reason", "resolved_at")
    search_fields = ("guide__title", "comment")
