"""The variance report is the honest stand-in for the determinism we do not
claim. Its aggregation math is tested here on synthetic repeated runs."""

from llm_testgen_bench.report import variance_md
from llm_testgen_bench.score import ScoreResult


def _result(model, task_id, kill_rate):
    return ScoreResult(
        task_id=task_id,
        failure_class="off_by_one",
        model=model,
        status="ok",
        valid=True,
        invalid_reason=None,
        total_mutants=10,
        killed=int(kill_rate * 10),
        survived=10 - int(kill_rate * 10),
        assertion_kills=int(kill_rate * 10),
        crash_kills=0,
        timeout_kills=0,
        kill_rate=kill_rate,
        assertion_kill_rate=kill_rate,
        prompt_tokens=0,
        completion_tokens=0,
        wall_seconds=0.0,
    )


def test_zero_variance_when_identical():
    run = [_result("m", "t01", 0.5)]
    md = variance_md([run, run, run])
    assert "0.000" in md  # spread column is zero
    assert "m" in md


def test_nonzero_variance_is_reported():
    r1 = [_result("m", "t01", 0.4)]
    r2 = [_result("m", "t01", 0.6)]
    md = variance_md([r1, r2])
    # spread = 0.2
    assert "0.200" in md


def test_multiple_models_each_row():
    run_a = [_result("m1", "t01", 0.3), _result("m2", "t01", 0.9)]
    run_b = [_result("m1", "t01", 0.5), _result("m2", "t01", 0.9)]
    md = variance_md([run_a, run_b])
    assert "m1" in md and "m2" in md
    # m2 identical across repeats -> spread 0
    lines = [ln for ln in md.splitlines() if ln.startswith("| m2")]
    assert lines and "0.000" in lines[0]
