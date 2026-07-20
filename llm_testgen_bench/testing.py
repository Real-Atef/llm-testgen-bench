"""Test/support utilities: a stub chat backend and a suite synthesizer.

These let the entire generate -> validate -> mutate -> score pipeline run with
NO Ollama server, which is what makes `bench selfcheck` and test_score.py
possible offline.
"""

from __future__ import annotations

from typing import Callable

from .corpus import CorpusTask
from .ollama_client import ChatResult

_BUILTIN_EXC = {
    "ValueError": "ValueError",
    "TypeError": "TypeError",
    "KeyError": "KeyError",
    "IndexError": "IndexError",
    "ZeroDivisionError": "ZeroDivisionError",
    "OverflowError": "OverflowError",
}


class StubClient:
    """A ChatBackend that returns canned text. ``reply`` is either a fixed
    string or a callable receiving the messages and returning the text."""

    def __init__(self, reply: str | Callable[[list[dict[str, str]]], str]):
        self._reply = reply
        self.calls = 0

    def chat(self, model, messages, *, temperature=0.0, seed=42) -> ChatResult:
        self.calls += 1
        text = self._reply(messages) if callable(self._reply) else self._reply
        return ChatResult(
            text=text,
            model=model,
            prompt_tokens=len(str(messages)),
            completion_tokens=len(text),
            wall_seconds=0.0,
            cached=False,
        )


def synth_suite_from_golden(task: CorpusTask) -> str:
    """Turn a task's hand-written golden cases into a real pytest file.

    The resulting suite is correct by construction (it encodes ground truth), so
    it passes on the correct impl and kills every mutant that changes any golden
    behaviour. Used as the 'perfect suite' baseline."""
    lines = ["import pytest", f"from impl import {task.entrypoint}", ""]
    for i, c in enumerate(task.golden_cases):
        call = f"{task.entrypoint}(*{c.args!r}, **{c.kwargs!r})"
        if c.raises:
            exc = _BUILTIN_EXC.get(c.raises, "Exception")
            lines += [
                f"def test_golden_{i}():",
                f"    with pytest.raises({exc}):",
                f"        {call}",
                "",
            ]
        else:
            lines += [
                f"def test_golden_{i}():",
                f"    assert {call} == {c.expected!r}",
                "",
            ]
    return "\n".join(lines)


def fenced(code: str) -> str:
    """Wrap code the way a well-behaved model would."""
    return f"Here is the test file:\n\n```python\n{code}\n```\n"


def trivial_suite(task: CorpusTask) -> str:
    """A valid-but-useless suite: it runs the function (so it imports and passes)
    but asserts nothing meaningful, so it should kill ~no mutants."""
    safe = next((c for c in task.golden_cases if not c.raises), None)
    if safe is None:
        call_line = "    pass\n"
    else:
        call_line = (
            f"    {task.entrypoint}(*{safe.args!r}, **{safe.kwargs!r})\n"
            "    assert True\n"
        )
    return (
        "import pytest\n"
        f"from impl import {task.entrypoint}\n\n"
        "def test_smoke_1():\n"
        f"{call_line}\n"
        "def test_smoke_2():\n"
        "    assert 1 == 1\n"
    )
