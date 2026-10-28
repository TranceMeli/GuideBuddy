"""Optional captcha (Cloudflare Turnstile). Switched off without a secret key."""

import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def captcha_enabled():
    return bool(settings.TURNSTILE_SECRET_KEY)


def verify_captcha(token, remote_ip=None):
    """True if the captcha was solved. Errors count as a failure."""
    if not captcha_enabled():
        return True
    if not token:
        return False
    data = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    request = urllib.request.Request(VERIFY_URL, data=urllib.parse.urlencode(data).encode())
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
            return bool(json.load(response).get("success"))
    except Exception:  # network error, invalid response ...
        logger.exception("Captcha verification failed")
        return False
