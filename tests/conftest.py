"""Shared fixtures. The harness tests never touch Ollama; only tests marked
``smoke`` do, and those are deselected by ``make test``."""

import pytest

from llm_testgen_bench.corpus import load_tasks


@pytest.fixture(scope="session")
def tasks():
    return load_tasks()
