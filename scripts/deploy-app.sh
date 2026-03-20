#!/usr/bin/env sh
set -eu

# Prepare python environment and run Django deploy tasks.
VENV_DIR="${VENV_DIR:-.venv}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-requirements.txt}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MANAGE_PY="${MANAGE_PY:-manage.py}"
PIP_BIN="$VENV_DIR/bin/pip"
PYTHON_VENV_BIN="$VENV_DIR/bin/python"

echo "Preparing virtual environment in $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

"$PIP_BIN" install --upgrade pip
"$PIP_BIN" install -r "$REQUIREMENTS_FILE"
"$PIP_BIN" install gunicorn

echo "Running Django migrations and collectstatic"
"$PYTHON_VENV_BIN" "$MANAGE_PY" migrate
"$PYTHON_VENV_BIN" "$MANAGE_PY" collectstatic --noinput
