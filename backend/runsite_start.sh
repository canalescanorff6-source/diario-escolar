#!/usr/bin/env bash
set -o errexit
mkdir -p staticfiles
# Garante que a pasta staticfiles exista também quando a plataforma pular o build.
python manage.py collectstatic --noinput --clear
python manage.py migrate --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-2} --timeout 120 --access-logfile - --error-logfile -
