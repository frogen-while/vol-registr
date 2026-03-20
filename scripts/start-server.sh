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

if command -v setsid >/dev/null 2>&1; then
  setsid "$VENV_GUNICORN" "$APP_MODULE" \
    --bind "$BIND_ADDR" \
    --workers "$WORKERS" \
    --timeout "$TIMEOUT" \
    --pid "$PIDFILE" \
    > "$LOGFILE" 2>&1 < /dev/null &
else
  nohup "$VENV_GUNICORN" "$APP_MODULE" \
    --bind "$BIND_ADDR" \
    --workers "$WORKERS" \
    --timeout "$TIMEOUT" \
    --pid "$PIDFILE" \
    > "$LOGFILE" 2>&1 < /dev/null &
fi

# Validate that a new gunicorn process is up.
i=0
while [ $i -lt 15 ]; do
  if [ -f "$PIDFILE" ]; then
    NEW_PID=$(cat "$PIDFILE" 2>/dev/null || true)
    if [ -n "$NEW_PID" ] && kill -0 "$NEW_PID" 2>/dev/null; then
      echo "Gunicorn started successfully with PID $NEW_PID"
      exit 0
    fi
  fi
  sleep 1
  i=$((i + 1))
done

echo "Error: gunicorn did not start successfully. Last log lines:"
tail -n 60 "$LOGFILE" 2>/dev/null || true
exit 1
