"""E-mails. In development they appear in the terminal of the Django server."""

from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from .tokens import email_verification_token, encode_uid


def _link(path, **params):
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}?{urlencode(params)}"


def _send(user_email, subject, body):
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user_email])


def send_verification_mail(user):
    link = _link(
        "/confirm",
        uid=encode_uid(user),
        token=email_verification_token.make_token(user),
    )
    _send(
        user.email,
        "Please confirm your e-mail address",
        f"Hello {user.username},\n\n"
        "welcome to GuideBuddy! Please confirm your e-mail address "
        "to activate your account:\n\n"
        f"{link}\n\n"
        "The link is valid for 24 hours. If you did not sign up, "
        "you can ignore this e-mail.\n",
    )


def send_already_registered_mail(email):
    """Sent instead of a confirmation when the address already has an account."""
    link = _link("/forgot-password")
    _send(
        email,
        "You already have a GuideBuddy account",
        "Hello,\n\n"
        "someone tried to create a new account with this e-mail address, "
        "but there already is one.\n\n"
        f"Forgot your password? You can reset it here:\n{link}\n\n"
        "If this was not you, you can ignore this e-mail.\n",
    )


def send_password_reset_mail(user):
    link = _link(
        "/reset-password",
        uid=encode_uid(user),
        token=default_token_generator.make_token(user),
    )
    _send(
        user.email,
        "Reset your password",
        f"Hello {user.username},\n\n"
        "a new password was requested for your GuideBuddy account:\n\n"
        f"{link}\n\n"
        "The link is valid for 24 hours. If you did not request this, "
        "you can ignore this e-mail – your password stays unchanged.\n",
    )
