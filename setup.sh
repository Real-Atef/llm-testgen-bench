#!/usr/bin/env sh
# One-shot setup: virtualenv, pinned dependencies, and a verification run.
# Usage:  ./setup.sh
set -e

echo "== 1/4  Creating virtual environment =="
python -m venv .venv

PY=".venv/bin/python"
[ -x "$PY" ] || PY=".venv/Scripts/python.exe"
if [ ! -x "$PY" ]; then
  echo "ERROR: could not find the venv interpreter." >&2
  exit 1
fi

echo "== 2/4  Installing pinned dependencies (requirements.lock) =="
"$PY" -m pip install --upgrade pip -q
"$PY" -m pip install -r requirements.lock -q

echo "== 3/4  Installing this package =="
"$PY" -m pip install -e . --no-deps -q

echo "== 4/4  Verifying: harness tests (no model calls) =="
"$PY" -m pytest -q -m "not smoke"

echo ""
echo "SETUP COMPLETE."
echo "Next:"
echo "  ./run.sh --smoke     # quick check against a tiny model (needs Ollama)"
echo "  ./run.sh             # full 3-model matrix"
