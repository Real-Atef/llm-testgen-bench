.PHONY: setup test smoke variance verify run report clean

PY ?= python

setup:
	$(PY) -m venv .venv
	.venv/bin/pip install -e ".[dev]" || .venv/Scripts/pip install -e ".[dev]"
	.venv/bin/pip freeze > requirements.lock || .venv/Scripts/pip freeze > requirements.lock

test:
	pytest -q -m "not smoke"

smoke:
	bench run --smoke && bench report

variance:
	bench run --smoke --repeat 3 && bench variance

verify: test smoke
	@echo VERIFIED

run:
	bench run --models qwen2.5-coder:7b,llama3.1:8b,qwen2.5:7b --tasks all --k 1

report:
	bench report

clean:
	rm -rf .bench_cache results/raw
