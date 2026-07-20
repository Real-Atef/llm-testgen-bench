"""Prompt construction, code-block extraction, and the generate-with-retry loop."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import settings
from .corpus import CorpusTask
from .ollama_client import ChatBackend

_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def load_prompt_template() -> str:
    return (settings.prompts_dir / "generate_tests.txt").read_text(encoding="utf-8")


def _docstring_of(source: str, entrypoint: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == entrypoint:
            return ast.get_docstring(node) or ""
    return ""


def build_prompt(task: CorpusTask) -> str:
    source = task.impl_source()
    return load_prompt_template().format(
        function_source=source.strip(),
        docstring=_docstring_of(source, task.entrypoint).strip() or "(see source)",
        entrypoint=task.entrypoint,
    )


def extract_code(text: str) -> str | None:
    """Pull a python test file out of a model response.

    Preference order:
      1. A fenced ```python block that mentions ``def test`` (or just the first
         fenced block if none do).
      2. Any fenced block.
      3. Heuristic: from the first ``import``/``def``/``from`` line to the end.
    Returns None if nothing plausible is found.
    """
    blocks = [m.group(1) for m in _FENCE_RE.finditer(text)]
    if blocks:
        for b in blocks:
            if "def test" in b:
                return b.strip()
        return blocks[0].strip()

    # No fences: take the largest run starting at an import/def/from.
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"\s*(import |from |def )", line):
            start = i
            break
    if start is None:
        return None
    return "\n".join(lines[start:]).strip() or None


@dataclass
class GenResult:
    task_id: str
    model: str
    status: str  # "ok" | "generation_error"
    test_source: str | None
    attempts: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    wall_seconds: float = 0.0
    transcript: list[dict[str, str]] = field(default_factory=list)
    error: str | None = None


def _valid_python(src: str) -> tuple[bool, str]:
    try:
        ast.parse(src)
        return True, ""
    except SyntaxError as exc:
        return False, f"SyntaxError: {exc}"


def generate_tests(
    client: ChatBackend,
    model: str,
    task: CorpusTask,
) -> GenResult:
    """Ask the model for a suite; one corrective retry on extraction/syntax
    failure; then give up with status='generation_error'."""
    prompt = build_prompt(task)
    messages = [{"role": "user", "content": prompt}]
    transcript: list[dict[str, str]] = []
    p_tok = c_tok = 0
    wall = 0.0

    for attempt in range(1, 3):  # up to 2 attempts
        res = client.chat(
            model, messages, temperature=settings.temperature, seed=settings.seed
        )
        p_tok += res.prompt_tokens
        c_tok += res.completion_tokens
        wall += res.wall_seconds
        transcript.append({"role": "assistant", "content": res.text})

        code = extract_code(res.text)
        if code is not None:
            ok, err = _valid_python(code)
            if ok:
                return GenResult(
                    task.id, model, "ok", code, attempt, p_tok, c_tok, wall, transcript
                )
            problem = err
        else:
            problem = "no python code block found in the response"

        # corrective feedback for the second attempt
        messages = messages + [
            {"role": "assistant", "content": res.text},
            {
                "role": "user",
                "content": (
                    f"That response could not be used ({problem}). Reply with ONLY "
                    f"a single ```python code block containing the complete pytest "
                    f"file, importing the function via `from impl import "
                    f"{task.entrypoint}`."
                ),
            },
        ]

    return GenResult(
        task.id, model, "generation_error", None, 2, p_tok, c_tok, wall, transcript,
        error=problem,
    )
