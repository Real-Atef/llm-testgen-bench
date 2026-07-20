#!/usr/bin/env python
"""Cross-platform mirror of `make verify` for users without Make.

Runs the harness tests (no model calls), then the smoke run (needs Ollama), and
prints VERIFIED only if both succeed.
"""

from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd).returncode


def main() -> int:
    py = sys.executable
    # 1) harness tests, no LLM
    rc = run([py, "-m", "pytest", "-q", "-m", "not smoke"])
    if rc != 0:
        print("harness tests failed", file=sys.stderr)
        return rc

    # 2) smoke run (needs a local Ollama server + the smoke model)
    rc = run([py, "-m", "llm_testgen_bench.cli", "run", "--smoke"])
    if rc != 0:
        print("smoke run failed (is Ollama running with the smoke model pulled?)",
              file=sys.stderr)
        return rc
    rc = run([py, "-m", "llm_testgen_bench.cli", "report"])
    if rc != 0:
        return rc

    print("\nVERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
