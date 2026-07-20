"""The corpus is the harness's ground truth. Every implementation must satisfy
its own hand-written golden cases, and every meta.yaml must validate. These
cases are never shown to models."""

import pytest

from llm_testgen_bench.corpus import load_tasks
from llm_testgen_bench.mutate import default_backend

TASKS = load_tasks()
TASK_IDS = [t.id for t in TASKS]

_EXC = {
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "IndexError": IndexError,
    "ZeroDivisionError": ZeroDivisionError,
    "OverflowError": OverflowError,
}


def test_corpus_has_21_tasks():
    assert len(TASKS) == 21


def test_three_tasks_per_failure_class():
    from collections import Counter

    counts = Counter(t.failure_class for t in TASKS)
    assert set(counts.values()) == {3}, counts
    assert len(counts) == 7


@pytest.mark.parametrize("task", TASKS, ids=TASK_IDS)
def test_impl_passes_golden_cases(task):
    fn = task.load_entrypoint()
    for i, c in enumerate(task.golden_cases):
        if c.raises:
            exc = _EXC.get(c.raises, Exception)
            with pytest.raises(exc):
                fn(*c.args, **c.kwargs)
        else:
            got = fn(*c.args, **c.kwargs)
            assert got == c.expected, f"case {i}: {got!r} != {c.expected!r}"


@pytest.mark.parametrize("task", TASKS, ids=TASK_IDS)
def test_impl_has_enough_mutable_operators(task):
    n = default_backend.count_mutable_operators(task.impl_source())
    assert n >= 4, f"{task.id} has only {n} mutable operators"


@pytest.mark.parametrize("task", TASKS, ids=TASK_IDS)
def test_meta_id_matches_folder(task):
    assert task.id == task.dir.name
    assert task.entrypoint  # non-empty
    assert len(task.golden_cases) >= 3
