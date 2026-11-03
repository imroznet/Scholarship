from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Delete temporary student photo uploads older than 24 hours."

    def handle(self, *args, **options):
        root = Path(settings.MEDIA_ROOT) / "private" / "tmp"
        if not root.exists():
            self.stdout.write("No temporary upload directory.")
            return
        cutoff = timezone.now() - timedelta(hours=24)
        removed = 0
        for path in root.iterdir():
            if not path.is_file():
                continue
            modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.get_current_timezone())
            if modified < cutoff:
                path.unlink()
                removed += 1
        self.stdout.write(f"Removed {removed} temporary file(s).")
