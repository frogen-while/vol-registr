#!/usr/bin/env sh
set -eu

# Stop running gunicorn process using pidfile and port fallback.
PIDFILE="${PIDFILE:-gunicorn.pid}"
PORT="${PORT:-8001}"

echo "Stopping old gunicorn processes..."

if [ -f "$PIDFILE" ]; then
  OLD_PID=$(cat "$PIDFILE" 2>/dev/null || true)
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Found gunicorn PID $OLD_PID from pidfile. Sending TERM signal."
    kill -TERM "$OLD_PID" 2>/dev/null || true
    i=0
    while [ $i -lt 15 ]; do
      if kill -0 "$OLD_PID" 2>/dev/null; then
        sleep 1
        i=$((i + 1))
      else
        break
      fi
    done
  else
    echo "Pidfile exists but process is not running."
  fi
  rm -f "$PIDFILE" || true
else
  echo "No pidfile found."
fi

PORT_PID=""
if command -v ss >/dev/null 2>&1; then
  PORT_PID=$(ss -ltnp 2>/dev/null | grep "0.0.0.0:$PORT\|127.0.0.1:$PORT" | grep -o 'pid=[0-9]*' | grep -o '[0-9]*' | head -n 1 || true)
elif command -v lsof >/dev/null 2>&1; then
  PORT_PID=$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)
fi

if [ -n "$PORT_PID" ]; then
  echo "Found process $PORT_PID listening on port $PORT. Sending TERM signal."
  kill -TERM "$PORT_PID" 2>/dev/null || true
  sleep 2
else
  echo "No listener process found for port $PORT (or lookup tools unavailable)."
fi

if command -v ss >/dev/null 2>&1; then
  if ss -ltn 2>/dev/null | grep -q ":$PORT"; then
    echo "Port $PORT is still busy! Forcing kill (best effort)..."
    PORT_PID=$(ss -ltnp 2>/dev/null | grep "0.0.0.0:$PORT\|127.0.0.1:$PORT" | grep -o 'pid=[0-9]*' | grep -o '[0-9]*' | head -n 1 || true)
    if [ -n "$PORT_PID" ]; then kill -9 "$PORT_PID" 2>/dev/null || true; fi
    sleep 2
  fi
elif command -v lsof >/dev/null 2>&1; then
  if lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $PORT is still busy! Forcing kill (best effort)..."
    PORT_PID=$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)
    if [ -n "$PORT_PID" ]; then kill -9 "$PORT_PID" 2>/dev/null || true; fi
    sleep 2
  fi
fi
