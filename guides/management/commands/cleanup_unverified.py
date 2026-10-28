from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = (
        "Delete accounts that did not confirm their e-mail address within a few days "
        "(frees the user name again). Banned accounts are kept."
    )

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=3, help="Older than this many days (default 3)")

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["days"])
        stale = User.objects.filter(
            is_active=False,
            is_superuser=False,
            date_joined__lt=cutoff,
            profile__isnull=False,  # only accounts from the registration
            profile__email_verified_at__isnull=True,
            profile__banned_at__isnull=True,
        )
        count = stale.count()
        stale.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} unconfirmed accounts."))
