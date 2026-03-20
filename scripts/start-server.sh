#!/usr/bin/env sh
set -eu

# Start gunicorn in background with configurable defaults.
APP_MODULE="${APP_MODULE:-vol_registr.wsgi:application}"
BIND_ADDR="${BIND_ADDR:-0.0.0.0:8001}"
WORKERS="${WORKERS:-3}"
TIMEOUT="${TIMEOUT:-120}"
PIDFILE="${PIDFILE:-gunicorn.pid}"
LOGFILE="${LOGFILE:-gunicorn.log}"
VENV_GUNICORN="${VENV_GUNICORN:-.venv/bin/gunicorn}"

echo "Starting gunicorn: $APP_MODULE on $BIND_ADDR"

setsid "$VENV_GUNICORN" "$APP_MODULE" \
  --bind "$BIND_ADDR" \
  --workers "$WORKERS" \
  --timeout "$TIMEOUT" \
  --pid "$PIDFILE" \
  > "$LOGFILE" 2>&1 < /dev/null &
