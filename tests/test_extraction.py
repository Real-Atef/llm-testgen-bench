"""Code-block extraction must tolerate the messy ways models wrap code."""

from llm_testgen_bench.generate import extract_code

CLEAN = "```python\nimport pytest\ndef test_a():\n    assert True\n```"
PROSE_AROUND = (
    "Sure! Here is the test file you asked for:\n\n"
    "```python\nimport pytest\ndef test_a():\n    assert 1 == 1\n```\n\n"
    "Let me know if you want more tests."
)
MULTIPLE_BLOCKS = (
    "First a helper example:\n```python\nx = 1\n```\n"
    "And the real suite:\n```python\nimport pytest\ndef test_real():\n    assert x\n```"
)
NO_FENCE = (
    "import pytest\n"
    "def test_nofence():\n    assert True\n"
)
BARE_FENCE = "```\nimport pytest\ndef test_b():\n    assert True\n```"


def test_clean_block():
    code = extract_code(CLEAN)
    assert "def test_a" in code
    assert "```" not in code


def test_prose_around_block():
    code = extract_code(PROSE_AROUND)
    assert code.startswith("import pytest")
    assert "Let me know" not in code


def test_prefers_block_with_tests():
    code = extract_code(MULTIPLE_BLOCKS)
    assert "def test_real" in code
    assert "helper example" not in code


def test_no_fence_heuristic():
    code = extract_code(NO_FENCE)
    assert "def test_nofence" in code


def test_bare_fence_without_language():
    code = extract_code(BARE_FENCE)
    assert "def test_b" in code


def test_returns_none_when_nothing_codey():
    assert extract_code("I cannot help with that.") is None
