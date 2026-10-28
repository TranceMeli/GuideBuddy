from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security, deploy=True)
def check_real_mailer(app_configs, **kwargs):
    """In production, e-mails must not end up in the terminal only."""
    backend = settings.MAILERS.get("default", {}).get("BACKEND", "")
    if backend.endswith("ReadableConsoleEmailBackend"):
        return [
            Error(
                "In production, e-mails are only written to the terminal.",
                hint="Set EMAIL_HOST (and credentials), so confirmation e-mails are sent.",
                id="guides.E001",
            )
        ]
    return []
