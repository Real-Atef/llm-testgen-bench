"""Run a generated pytest suite against an implementation, in isolation.

Cross-platform: uses ``subprocess`` + ``timeout`` only. No ``resource`` module,
no POSIX-only calls, so it behaves the same on Windows, macOS, and Linux.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .config import settings

Status = Literal["passed", "failed", "error", "timeout"]

_SUMMARY_RE = re.compile(
    r"(?:(\d+) failed)?.*?(?:(\d+) passed)?.*?(?:(\d+) error(?:s)?)?", re.IGNORECASE
)


@dataclass
class SandboxResult:
    status: Status
    returncode: int | None
    passed: int
    failed: int
    errors: int
    duration: float
    stdout: str
    stderr: str

    @property
    def all_passed(self) -> bool:
        return self.status == "passed"


def _counts(output: str) -> tuple[int, int, int]:
    passed = failed = errors = 0
    for m in re.finditer(r"(\d+)\s+(passed|failed|error(?:s)?)", output):
        n = int(m.group(1))
        kind = m.group(2)
        if kind == "passed":
            passed = n
        elif kind == "failed":
            failed = n
        else:
            errors = n
    return passed, failed, errors


def run_suite(
    impl_source: str,
    test_source: str,
    *,
    timeout: float | None = None,
) -> SandboxResult:
    """Write ``impl.py`` + the test file into a temp dir and run pytest there.

    Exit-code mapping (pytest convention):
      0 -> passed        all collected tests passed
      1 -> failed        one or more tests failed
      2/3/4 -> error     interrupted / internal / usage error
      5 -> error         no tests collected (an empty or non-importing suite)
    """
    timeout = timeout if timeout is not None else settings.sandbox_timeout
    import time

    with tempfile.TemporaryDirectory(prefix="testgen_") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "impl.py").write_text(impl_source, encoding="utf-8")
        (tmp_path / "test_generated.py").write_text(test_source, encoding="utf-8")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "test_generated.py",
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
        ]
        env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(tmp_path)}
        # Inherit PATH etc. but force our two vars.
        import os

        full_env = {**os.environ, **env}

        start = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                cwd=tmp,
                env=full_env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - start
            return SandboxResult(
                status="timeout",
                returncode=None,
                passed=0,
                failed=0,
                errors=0,
                duration=duration,
                stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
                stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
            )

        duration = time.perf_counter() - start
        rc = proc.returncode
        combined = proc.stdout + "\n" + proc.stderr
        passed, failed, errors = _counts(combined)

        if rc == 0:
            status: Status = "passed"
        elif rc == 1:
            status = "failed"
        else:  # 2,3,4,5 and anything else
            status = "error"

        return SandboxResult(
            status=status,
            returncode=rc,
            passed=passed,
            failed=failed,
            errors=errors,
            duration=duration,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
