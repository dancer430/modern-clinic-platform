#!/usr/bin/env sh
set -eu

echo "[bootstrap] waiting for database..."
python - <<'PY'
import os
import time
import psycopg2

db = os.getenv("POSTGRES_DB")
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))

for i in range(60):
    try:
        conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
        conn.close()
        print("[bootstrap] database is ready")
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("[bootstrap] database not ready after timeout")
PY

echo "[bootstrap] running migrations..."
python manage.py migrate --noinput

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  echo "[bootstrap] ensuring superuser exists..."
  python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from users.models import User

username = os.environ["DJANGO_SUPERUSER_USERNAME"]
email = os.environ["DJANGO_SUPERUSER_EMAIL"]
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]

user = User._default_manager.filter(username=username).first()
if user is None:
    User._default_manager.create_superuser(username=username, email=email, password=password)
    print("[bootstrap] superuser created")
else:
    changed = False
    if email and user.email != email:
        user.email = email
        changed = True
    if not user.is_superuser or not user.is_staff:
        user.is_superuser = True
        user.is_staff = True
        changed = True
    if changed:
        user.save(update_fields=["email", "is_superuser", "is_staff"])
    print("[bootstrap] superuser already exists")
PY
else
  echo "[bootstrap] superuser env not fully set, skipping auto-create"
fi

echo "[bootstrap] starting gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
