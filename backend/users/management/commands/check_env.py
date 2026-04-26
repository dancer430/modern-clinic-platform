"""``manage.py check_env`` — print env-var presence and exit non-zero on missing.

Useful in container start scripts: run before serving traffic to fail fast
when a deployment forgot to set a required variable.
"""

from __future__ import annotations

import os
import sys

from django.core.management.base import BaseCommand

from config.settings import REQUIRED_PROD_ENV


class Command(BaseCommand):
    help = "Print presence of required production env vars and exit non-zero if any are missing."

    def handle(self, *args, **options):
        missing: list[str] = []
        for name in REQUIRED_PROD_ENV:
            present = os.getenv(name)
            self.stdout.write(f"{name}: {'set' if present else 'MISSING'}")
            if not present:
                missing.append(name)
        if missing:
            self.stderr.write(self.style.ERROR(f"missing: {', '.join(missing)}"))
            sys.exit(1)
