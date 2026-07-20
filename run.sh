#!/usr/bin/env sh
# Run the benchmark and render the leaderboard.
# Usage:
#   ./run.sh                 full default matrix (3 models x 21 tasks)
#   ./run.sh --smoke         2 easiest tasks against the smoke model
#   ./run.sh <model[,model]> a specific model or comma-separated list
set -e

PY=".venv/bin/python"
[ -x "$PY" ] || PY=".venv/Scripts/python.exe"
if [ ! -x "$PY" ]; then
  echo "No virtualenv found. Run ./setup.sh first." >&2
  exit 1
fi

# Ollama must be up: every run needs local inference.
if ! curl -sf http://localhost:11434/v1/models >/dev/null 2>&1; then
  echo "ERROR: Ollama is not reachable at http://localhost:11434" >&2
  echo "Start it with 'ollama serve', then pull a model, e.g.:" >&2
  echo "  ollama pull qwen2.5-coder:7b" >&2
  exit 1
fi

case "$1" in
  --smoke)
    echo "== Smoke run: 2 easiest tasks x smoke model =="
    "$PY" -m llm_testgen_bench.cli run --smoke
    ;;
  "")
    echo "== Full matrix: qwen2.5-coder:7b, llama3.1:8b, qwen2.5:7b x 21 tasks =="
    echo "   (CPU-bound; expect roughly an hour)"
    "$PY" -m llm_testgen_bench.cli run \
      --models qwen2.5-coder:7b,llama3.1:8b,qwen2.5:7b --tasks all --k 1
    ;;
  *)
    echo "== Custom run: $1 =="
    "$PY" -m llm_testgen_bench.cli run --models "$1" --tasks all --k 1
    ;;
esac

"$PY" -m llm_testgen_bench.cli report
echo ""
echo "Done. See results/leaderboard.md and results/kill_rates.png"
