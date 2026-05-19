#!/usr/bin/env bash
set -o errexit
python manage.py migrate --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-2} --timeout 120 --access-logfile - --error-logfile -
