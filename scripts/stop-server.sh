#!/usr/bin/env sh
set -u

# Stop running gunicorn process using pidfile and port fallback.
PIDFILE="${PIDFILE:-gunicorn.pid}"
PORT="${PORT:-8001}"

echo "Stopping old gunicorn processes (best effort)..."

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

find_gunicorn_pid() {
  if command_exists pgrep; then
    pgrep -f "gunicorn" 2>/dev/null | head -n 1
    return 0
  fi

  return 1
}

find_listener_pid() {
  if command_exists ss; then
    ss -ltnp 2>/dev/null \
      | awk -v port=":$PORT" '$0 ~ port { if (match($0, /pid=[0-9]+/)) { print substr($0, RSTART + 4, RLENGTH - 4); exit } }'
    return 0
  fi

  if command_exists lsof; then
    lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1
    return 0
  fi

  if command_exists netstat; then
    netstat -ltnp 2>/dev/null \
      | awk -v port=":$PORT" '$4 ~ port"$" { split($7, a, "/"); if (a[1] ~ /^[0-9]+$/) { print a[1]; exit } }'
    return 0
  fi

  find_gunicorn_pid 2>/dev/null || true
  return 0

  return 1
}

is_port_busy() {
  if command_exists ss; then
    ss -ltn 2>/dev/null | awk -v port=":$PORT" '$0 ~ port { found=1 } END { exit(found ? 0 : 1) }'
    return $?
  fi

  if command_exists lsof; then
    lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi

  if command_exists netstat; then
    netstat -ltn 2>/dev/null | awk -v port=":$PORT" '$4 ~ port"$" { found=1 } END { exit(found ? 0 : 1) }'
    return $?
  fi

  if command_exists nc; then
    nc -z 127.0.0.1 "$PORT" >/dev/null 2>&1
    return $?
  fi

  if command_exists pgrep; then
    pgrep -f "gunicorn" >/dev/null 2>&1
    return $?
  fi

  return 1
}

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
PORT_PID=$(find_listener_pid 2>/dev/null || true)

if [ -n "$PORT_PID" ]; then
  echo "Found process $PORT_PID listening on port $PORT. Sending TERM signal."
  kill -TERM "$PORT_PID" 2>/dev/null || true
  sleep 2
else
  echo "No listener process found for port $PORT."
fi

if is_port_busy; then
  echo "Port $PORT is still busy. Forcing kill (best effort)..."
  PORT_PID=$(find_listener_pid 2>/dev/null || true)
  if [ -n "$PORT_PID" ]; then
    kill -KILL "$PORT_PID" 2>/dev/null || true
    sleep 2
  else
    echo "Could not resolve PID for busy port $PORT."
  fi
fi

if is_port_busy; then
  echo "Error: port $PORT is still busy after stop attempts."
  exit 1
else
  echo "Port $PORT is free."
fi

exit 0
