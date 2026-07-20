"""pymutant: correct count, all compile, no duplicates, deterministic."""

from llm_testgen_bench.mutate import PyMutant, default_backend

FIXTURE = '''def f(x):
    if x < 10:
        return x + 1
    return 0
'''


def test_expected_mutant_count():
    muts = default_backend.generate(FIXTURE)
    # 2 returns + 1 comparison + 3 int constants (0,10,1) + 1 arithmetic = 7
    assert len(muts) == 7


def test_all_mutants_compile():
    for m in default_backend.generate(FIXTURE):
        compile(m.source, "<mutant>", "exec")  # raises if broken


def test_no_duplicate_mutants():
    muts = default_backend.generate(FIXTURE)
    sources = [m.source for m in muts]
    assert len(set(sources)) == len(sources)


def test_original_not_among_mutants():
    import ast

    original = ast.unparse(ast.parse(FIXTURE))
    for m in default_backend.generate(FIXTURE):
        assert m.source != original


def test_determinism():
    a = default_backend.generate(FIXTURE)
    b = default_backend.generate(FIXTURE)
    assert [m.source for m in a] == [m.source for m in b]
    assert [m.operator for m in a] == [m.operator for m in b]


def test_operators_present():
    ops = {m.operator for m in default_backend.generate(FIXTURE)}
    assert {"comparison", "arithmetic", "constant", "return"} <= ops


def test_comparison_swap_direction():
    muts = default_backend.generate("def g(a, b):\n    return a < b\n")
    assert any(m.mutation == "Lt->LtE" for m in muts)


def test_boolean_and_not_operators():
    src = "def h(a, b):\n    return a and not b\n"
    ops = {m.mutation for m in PyMutant().generate(src)}
    assert "And->Or" in ops
    assert "drop-not" in ops


def test_boundary_label_for_slice_and_range():
    src = "def s(xs):\n    return xs[2:] + list(range(3))\n"
    muts = default_backend.generate(src)
    assert any(m.operator == "boundary" for m in muts)


def test_cap_is_respected():
    from llm_testgen_bench.config import settings

    # a function with many int constants
    body = " + ".join(str(i) for i in range(100))
    src = f"def big():\n    return {body}\n"
    muts = default_backend.generate(src)
    assert len(muts) <= settings.max_mutants
