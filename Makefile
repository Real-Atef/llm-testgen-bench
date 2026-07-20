.PHONY: setup test smoke variance verify run report validate selfcheck clean

# Prefer the project venv interpreter if present (Windows Scripts/ or POSIX bin/),
# else fall back to whatever `python` is on PATH.
VENV_PY := $(wildcard .venv/Scripts/python.exe .venv/bin/python)
PY := $(if $(VENV_PY),$(firstword $(VENV_PY)),python)
BENCH := $(PY) -m llm_testgen_bench.cli

setup:
	python -m venv .venv
	$(PY) -m pip install -e ".[dev]"
	$(PY) -m pip freeze | grep -viE "^-e|llm-testgen-bench" > requirements.lock

test:
	$(PY) -m pytest -q -m "not smoke"

smoke:
	$(BENCH) run --smoke && $(BENCH) report

variance:
	$(BENCH) run --smoke --repeat 3 && $(BENCH) variance

validate:
	$(BENCH) validate

selfcheck:
	$(BENCH) selfcheck

verify: test smoke
	@echo VERIFIED

run:
	$(BENCH) run --models qwen2.5-coder:7b,llama3.1:8b,qwen2.5:7b --tasks all --k 1

report:
	$(BENCH) report

clean:
	rm -rf .bench_cache results/raw
