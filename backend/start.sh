#!/bin/sh
# Container entrypoint (Docker / Railway): migrate, optional first-run setup, then serve on $PORT.
set -e
python manage.py migrate --noinput

# Optional: create the first super admin (set DJANGO_SUPERUSER_USERNAME / _PASSWORD / _EMAIL once, then remove them).
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput 2>/dev/null && echo "Super admin $DJANGO_SUPERUSER_USERNAME created." \
    || echo "Super admin $DJANGO_SUPERUSER_USERNAME already exists."
fi

# Load the public website content (only when the website has none yet).
if [ "${SEED_WEBSITE:-true}" = "true" ]; then
  python manage.py seed_website || true
fi

exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-3}" --timeout 120 --access-logfile -
