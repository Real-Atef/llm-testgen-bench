"""Corpus loading and validation.

A task lives in ``corpus/tasks/<id>/`` with:
  * ``impl.py``  - exactly one public function (the ``entrypoint``) + docstring
  * ``meta.yaml`` - metadata + hand-written ``golden_cases`` (the harness's
    hidden ground truth, never shown to models)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from .config import settings

FailureClass = Literal[
    "off_by_one",
    "empty_and_none",
    "unicode_text",
    "float_precision",
    "mutation_aliasing",
    "ordering_stability",
    "parsing_validation",
]


class GoldenCase(BaseModel):
    """One ground-truth input/output pair. Either ``expected`` (a value the
    call must equal) or ``raises`` (an exception type name) must describe the
    outcome."""

    model_config = {"extra": "forbid"}

    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    expected: Any = None
    raises: str | None = None
    note: str | None = None


class CorpusTask(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    title: str
    difficulty: int = Field(ge=1, le=3)
    failure_class: FailureClass
    entrypoint: str
    description: str
    golden_cases: list[GoldenCase] = Field(min_length=3)

    # populated at load time, not from yaml
    dir: Path = Field(exclude=True, default=None)  # type: ignore[assignment]

    @model_validator(mode="after")
    def _check(self) -> "CorpusTask":
        if self.dir is not None:
            impl = self.dir / "impl.py"
            if not impl.exists():
                raise ValueError(f"{self.id}: missing impl.py")
        return self

    @property
    def impl_path(self) -> Path:
        return self.dir / "impl.py"

    def impl_source(self) -> str:
        return self.impl_path.read_text(encoding="utf-8")

    def load_entrypoint(self) -> Callable[..., Any]:
        """Import impl.py in isolation and return the entrypoint callable."""
        spec = importlib.util.spec_from_file_location(
            f"corpus_{self.id}", self.impl_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {self.impl_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fn = getattr(module, self.entrypoint, None)
        if fn is None:
            raise AttributeError(
                f"{self.id}: entrypoint {self.entrypoint!r} not defined in impl.py"
            )
        return fn


def load_task(task_dir: Path) -> CorpusTask:
    meta = yaml.safe_load((task_dir / "meta.yaml").read_text(encoding="utf-8"))
    task = CorpusTask(**meta, dir=task_dir)
    if task.id != task_dir.name:
        raise ValueError(f"id {task.id!r} != folder {task_dir.name!r}")
    return task


def load_tasks(corpus_dir: Path | None = None) -> list[CorpusTask]:
    root = corpus_dir or settings.corpus_dir
    tasks = [
        load_task(d)
        for d in sorted(root.iterdir())
        if d.is_dir() and (d / "meta.yaml").exists()
    ]
    if not tasks:
        raise RuntimeError(f"no tasks found under {root}")
    return tasks


def get_task(task_id: str, corpus_dir: Path | None = None) -> CorpusTask:
    for t in load_tasks(corpus_dir):
        if t.id == task_id:
            return t
    raise KeyError(task_id)
