"""Who may do what? Central rules for the API and the Django pages."""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.permissions import SAFE_METHODS, BasePermission

MODERATOR_GROUP = "Moderatoren"


def is_moderator(user):
    if not (user and user.is_authenticated and user.is_active):
        return False
    return user.is_superuser or user.groups.filter(name=MODERATOR_GROUP).exists()


def _profile(user):
    return getattr(user, "profile", None)


def waiting_hours_left(user):
    """How many hours a new account still has to wait (0 = may write)."""
    hours = settings.NEW_ACCOUNT_WAIT_HOURS
    if hours <= 0:
        return 0
    profile = _profile(user)
    start = (profile.email_verified_at if profile else None) or user.date_joined
    remaining = start + timedelta(hours=hours) - timezone.now()
    return max(0, int(remaining.total_seconds() // 3600) + (1 if remaining.total_seconds() % 3600 else 0))


def write_denial(user, guide=None):
    """Return an error message if the user may not write, otherwise None."""
    if not (user and user.is_authenticated):
        return "Please sign in."
    if is_moderator(user):
        return None
    profile = _profile(user)
    if profile and profile.banned:
        return "Your account is banned."
    left = waiting_hours_left(user)
    if left:
        return (
            f"New accounts may edit guides {settings.NEW_ACCOUNT_WAIT_HOURS} hours after "
            f"confirming their e-mail address. About {left} hour(s) to go."
        )
    if guide is not None and guide.is_locked:
        return "This guide is locked. Only moderators may edit it."
    return None


class CanWrite(BasePermission):
    """Write access to guides: account rules on create, plus the lock on change."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        message = write_denial(request.user)
        if message:
            self.message = message
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        message = write_denial(request.user, obj)
        if message:
            self.message = message
            return False
        return True


def delete_denial(user, guide):
    """Return an error message if the user may not delete this guide, otherwise None.

    Only the author and moderators may delete; the usual write rules (ban, waiting period,
    lock) apply on top.
    """
    message = write_denial(user, guide)
    if message:
        return message
    if is_moderator(user) or (guide.created_by_id is not None and guide.created_by_id == user.pk):
        return None
    return "Only the author and moderators can delete this guide."


class CanDelete(BasePermission):
    def has_object_permission(self, request, view, obj):
        message = delete_denial(request.user, obj)
        if message:
            self.message = message
            return False
        return True


class IsModerator(BasePermission):
    message = "Moderators only."

    def has_permission(self, request, view):
        return is_moderator(request.user)
