"""Scoring: generate a suite, check it is valid, then measure its mutation
kill rate against the implementation.

Kill accounting is deliberately split so that "the suite actually asserts
behaviour" is not confused with "a mutant happened to crash":

  assertion_kill : a mutant made a test FAIL (a real, behavioural catch)
  crash_kill     : a mutant made the suite ERROR (import/exception) - trivially
                   caught by any suite that runs the function
  timeout_kill   : a mutant made the suite hang past the per-mutant timeout

kill_rate counts all three (a killed mutant is killed). assertion_kill_rate is
the honest headline: how many mutants the suite caught *by testing behaviour*.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .config import settings
from .corpus import CorpusTask
from .generate import GenResult, generate_tests
from .mutate import Mutant, default_backend
from .ollama_client import ChatBackend
from .sandbox import run_suite


@dataclass
class MutantOutcome:
    index: int
    operator: str
    mutation: str
    lineno: int
    status: str  # sandbox status: passed(survived)/failed/error/timeout
    killed: bool
    kill_kind: str | None  # "assertion" | "crash" | "timeout" | None


@dataclass
class ScoreResult:
    task_id: str
    failure_class: str
    model: str
    status: str  # "ok" | "generation_error" | "invalid"
    valid: bool
    invalid_reason: str | None
    total_mutants: int
    killed: int
    survived: int
    assertion_kills: int
    crash_kills: int
    timeout_kills: int
    kill_rate: float
    assertion_kill_rate: float
    prompt_tokens: int
    completion_tokens: int
    wall_seconds: float
    test_source: str | None = None
    mutants: list[MutantOutcome] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def _empty(task: CorpusTask, model: str, status: str, reason: str | None,
           gen: GenResult | None) -> ScoreResult:
    return ScoreResult(
        task_id=task.id,
        failure_class=task.failure_class,
        model=model,
        status=status,
        valid=False,
        invalid_reason=reason,
        total_mutants=0,
        killed=0,
        survived=0,
        assertion_kills=0,
        crash_kills=0,
        timeout_kills=0,
        kill_rate=0.0,
        assertion_kill_rate=0.0,
        prompt_tokens=gen.prompt_tokens if gen else 0,
        completion_tokens=gen.completion_tokens if gen else 0,
        wall_seconds=gen.wall_seconds if gen else 0.0,
        test_source=gen.test_source if gen else None,
    )


def score_task(
    client: ChatBackend,
    model: str,
    task: CorpusTask,
    *,
    mutants: list[Mutant] | None = None,
) -> ScoreResult:
    gen = generate_tests(client, model, task)
    if gen.status != "ok" or gen.test_source is None:
        return _empty(task, model, "generation_error", gen.error, gen)

    impl_source = task.impl_source()
    test_source = gen.test_source

    # 1) validity: tests must pass against the correct implementation.
    base = run_suite(impl_source, test_source, timeout=settings.sandbox_timeout)
    if not base.all_passed:
        reason = f"tests_{base.status}_on_correct_impl"
        return _empty(task, model, "invalid", reason, gen)

    # 2) mutation scoring.
    muts = mutants if mutants is not None else default_backend.generate(impl_source)
    outcomes: list[MutantOutcome] = []
    assertion = crash = timeout = 0
    for m in muts:
        r = run_suite(m.source, test_source, timeout=settings.mutant_timeout)
        if r.status == "failed":
            killed, kind = True, "assertion"
            assertion += 1
        elif r.status == "error":
            killed, kind = True, "crash"
            crash += 1
        elif r.status == "timeout":
            killed, kind = True, "timeout"
            timeout += 1
        else:  # passed -> mutant survived
            killed, kind = False, None
        outcomes.append(
            MutantOutcome(m.index, m.operator, m.mutation, m.lineno, r.status, killed, kind)
        )

    total = len(muts)
    killed = assertion + crash + timeout
    survived = total - killed
    kill_rate = killed / total if total else 0.0
    assertion_rate = assertion / total if total else 0.0

    return ScoreResult(
        task_id=task.id,
        failure_class=task.failure_class,
        model=model,
        status="ok",
        valid=True,
        invalid_reason=None,
        total_mutants=total,
        killed=killed,
        survived=survived,
        assertion_kills=assertion,
        crash_kills=crash,
        timeout_kills=timeout,
        kill_rate=kill_rate,
        assertion_kill_rate=assertion_rate,
        prompt_tokens=gen.prompt_tokens,
        completion_tokens=gen.completion_tokens,
        wall_seconds=gen.wall_seconds,
        test_source=test_source,
        mutants=outcomes,
    )
