import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = (
        "Back up the SQLite database while it is running (sqlite3 backup API, "
        "consistent even with concurrent access) and delete old backups."
    )

    def add_arguments(self, parser):
        parser.add_argument("--keep", type=int, default=14, help="Number of backups to keep (default 14)")
        parser.add_argument("--target-dir", default=None, help="Target folder (default: BACKUP_DIR)")
        parser.add_argument("--source", default=None, help="Database file (default: current database)")

    def handle(self, *args, **options):
        source = options["source"] or connection.settings_dict["NAME"]
        source = Path(str(source))
        if not source.is_file():
            raise CommandError(f"Database file not found: {source}")
        target_dir = Path(options["target_dir"] or settings.BACKUP_DIR)
        target_dir.mkdir(parents=True, exist_ok=True)

        stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
        target = target_dir / f"db-{stamp}.sqlite3"

        source_conn = sqlite3.connect(source)
        target_conn = sqlite3.connect(target)
        try:
            source_conn.backup(target_conn)
        finally:
            target_conn.close()
            source_conn.close()

        old = sorted(target_dir.glob("db-*.sqlite3"), reverse=True)[max(options["keep"], 1):]
        for path in old:
            path.unlink()
        self.stdout.write(self.style.SUCCESS(f"Backup created: {target} (deleted {len(old)} old ones)"))
