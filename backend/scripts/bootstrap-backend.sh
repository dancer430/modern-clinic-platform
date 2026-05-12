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

if [ -n "${MINIO_ENDPOINT:-}" ] && [ -n "${MINIO_ROOT_USER:-}" ] && [ -n "${MINIO_ROOT_PASSWORD:-}" ]; then
  echo "[bootstrap] configuring MinIO bucket..."
  mc alias set local "$MINIO_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
  if ! mc ls "local/${MINIO_BUCKET:-clinic-media}" >/dev/null 2>&1; then
    mc mb "local/${MINIO_BUCKET:-clinic-media}"
  fi
  # Public read for media/ prefix only.
  cat > /tmp/policy.json <<'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::__BUCKET__/media/*"]
    }
  ]
}
POLICY
  sed -i "s/__BUCKET__/${MINIO_BUCKET:-clinic-media}/g" /tmp/policy.json
  mc anonymous set-json /tmp/policy.json "local/${MINIO_BUCKET:-clinic-media}" || true
  echo "[bootstrap] MinIO bucket ready"
fi

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
    user = User._default_manager.create_superuser(username=username, email=email, password=password)
    if user.role != User.Role.ADMIN:
        user.role = User.Role.ADMIN
        user.save(update_fields=["role"])
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
    if user.role != User.Role.ADMIN:
        user.role = User.Role.ADMIN
        changed = True
    if not user.check_password(password):
        user.set_password(password)
        changed = True
    if changed:
        user.save(update_fields=["email", "is_superuser", "is_staff", "role", "password"])
    print("[bootstrap] superuser already exists")
PY
else
  echo "[bootstrap] superuser env not fully set, skipping auto-create"
fi

echo "[bootstrap] starting gunicorn..."
GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_MAX_REQUESTS="${GUNICORN_MAX_REQUESTS:-1000}"
GUNICORN_MAX_REQUESTS_JITTER="${GUNICORN_MAX_REQUESTS_JITTER:-100}"

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS}" \
  --timeout "${GUNICORN_TIMEOUT}" \
  --max-requests "${GUNICORN_MAX_REQUESTS}" \
  --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}"
