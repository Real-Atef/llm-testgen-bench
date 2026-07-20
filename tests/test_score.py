"""End-to-end scoring with a stub model client (no Ollama):
  perfect suite  -> valid, high kill rate
  trivial suite  -> valid, ~zero kill rate
  failing suite  -> invalid
  broken output  -> generation_error
"""

import pytest

from llm_testgen_bench.corpus import get_task
from llm_testgen_bench.score import score_task
from llm_testgen_bench.testing import (
    StubClient,
    fenced,
    synth_suite_from_golden,
    trivial_suite,
)

TASK_ID = "t16_stable_rank"  # small, deterministic, no float edge cases


@pytest.fixture
def task():
    return get_task(TASK_ID)


def test_perfect_suite_is_valid_and_kills(task):
    client = StubClient(fenced(synth_suite_from_golden(task)))
    r = score_task(client, "stub", task)
    assert r.valid
    assert r.status == "ok"
    assert r.total_mutants > 0
    assert r.kill_rate > 0.5
    assert r.assertion_kills > 0


def test_trivial_suite_is_valid_but_weak(task):
    client = StubClient(fenced(trivial_suite(task)))
    r = score_task(client, "stub", task)
    assert r.valid  # it runs and passes on the correct impl
    assert r.kill_rate < 0.3  # but it barely catches anything


def test_failing_suite_is_invalid(task):
    bad = (
        f"from impl import {task.entrypoint}\n"
        "def test_wrong():\n"
        f"    assert {task.entrypoint}([1, 2, 3]) == 'nonsense'\n"
    )
    client = StubClient(fenced(bad))
    r = score_task(client, "stub", task)
    assert not r.valid
    assert r.status == "invalid"
    assert r.kill_rate == 0.0


def test_unparseable_output_is_generation_error(task):
    client = StubClient("I refuse to write tests. No code here.")
    r = score_task(client, "stub", task)
    assert r.status == "generation_error"
    assert not r.valid


def test_perfect_beats_trivial(task):
    perfect = score_task(StubClient(fenced(synth_suite_from_golden(task))), "s", task)
    trivial = score_task(StubClient(fenced(trivial_suite(task))), "s", task)
    assert perfect.kill_rate > trivial.kill_rate
