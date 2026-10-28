"""Login with JWT (access and refresh token).

The browser never sees the tokens: the Nuxt server keeps them in HttpOnly cookies and sends
the access token to Django as "Authorization: Bearer ...".

- Access token: short-lived (see SIMPLE_JWT in settings.py), checked on every request.
- Refresh token: longer-lived, exchanged on every renewal (rotation); the old one is then
  on the blocklist.
- When the password changes, all earlier tokens become invalid automatically
  (claim "hash_password"). Banned or deleted accounts are rejected immediately.
"""

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken


class SoftJWTAuthentication(JWTAuthentication):
    """JWT login that ignores an invalid token on read requests.

    Otherwise an expired or revoked token would block public pages with "401", too.
    Write requests stay strict.
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (AuthenticationFailed, InvalidToken, TokenError):
            if request.method in SAFE_METHODS:
                return None
            raise


def issue_tokens(user):
    """A new token pair for a user."""
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def revoke_user_tokens(user):
    """Put all refresh tokens of a user on the blocklist (sign out everywhere)."""
    for outstanding in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding)


def revoke_refresh_token(raw_token):
    """Revoke a single refresh token. Invalid tokens are silently ignored."""
    try:
        RefreshToken(raw_token).blacklist()
    except TokenError:
        pass
