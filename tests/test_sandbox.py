"""The sandbox must correctly classify passing, failing, erroring, and hanging
suites. These are real subprocess pytest runs (no LLM)."""

from llm_testgen_bench.sandbox import run_suite

IMPL = "def add(a, b):\n    return a + b\n"


def test_passing_suite_passes():
    test = (
        "from impl import add\n"
        "def test_ok():\n    assert add(1, 2) == 3\n"
    )
    r = run_suite(IMPL, test)
    assert r.status == "passed"
    assert r.all_passed
    assert r.passed >= 1


def test_failing_suite_fails():
    test = (
        "from impl import add\n"
        "def test_bad():\n    assert add(1, 2) == 99\n"
    )
    r = run_suite(IMPL, test)
    assert r.status == "failed"
    assert not r.all_passed


def test_import_error_is_error():
    test = "from impl import does_not_exist\ndef test_x():\n    assert True\n"
    r = run_suite(IMPL, test)
    assert r.status == "error"


def test_no_tests_collected_is_error():
    test = "from impl import add\n# no test functions here\n"
    r = run_suite(IMPL, test)
    assert r.status == "error"


def test_infinite_loop_times_out():
    test = (
        "from impl import add\n"
        "def test_hang():\n    while True:\n        pass\n"
    )
    r = run_suite(IMPL, test, timeout=5)
    assert r.status == "timeout"
    assert r.duration >= 4  # it actually waited near the timeout


def test_syntactically_broken_suite_is_error():
    test = "from impl import add\ndef test_x(:\n    pass\n"
    r = run_suite(IMPL, test)
    assert r.status == "error"
