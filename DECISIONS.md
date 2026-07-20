# Decisions

One entry per non-obvious choice: what, why, and what was rejected.

## Corpus cut to 21 tasks (3 per failure class), not 50

The original plan called for 50 tasks. The corpus is the harness's ground truth —
if any `impl.py` is subtly wrong, every kill rate computed against it is garbage,
and the hidden sanity tests won't catch it because they'd share the same blind spot.
21 tasks (3 per failure class) is the largest set I could personally verify by hand
and re-verify by execution. **20-ish verified tasks beat 50 unverified ones.** Adding
more is easy later (`corpus/tasks/<id>/` + a row in the taxonomy).

## Determinism is measured, not claimed

The spec asked for `temperature=0, seed=42` "for determinism." That does **not**
give byte-identical output through Ollama: the OpenAI-compatible endpoint does not
reliably honor `seed`, and batching / GPU scheduling / version drift all break
reproducibility. Rather than assert a false invariant, the harness ships
`bench run --repeat N` + `bench variance`, which re-samples and reports the run-to-run
spread in kill rate. **A measured variance number is a stronger portfolio signal than
a determinism claim a reviewer can falsify in one command.** See README > Reproducibility.

## Variance runs bypass the response cache

The on-disk cache (keyed by `sha256(model+messages+params)`) makes the benchmark
resumable and free to re-run. But it would make every `--repeat` identical, so
variance would trivially read `0.000` and *look* like the determinism we just said
we don't have. `--repeat > 1` therefore forces `--no-cache` so each repeat is a fresh
sample. The engine may still be reproducible on a given machine (CPU greedy decoding
often is) — that's a legitimate measured result, not an assumption.

## Crash-kills tracked separately from assertion-kills

A mutant that makes the suite **error** (import/exception) is caught by any suite that
merely runs the function — that is not evidence the suite tests behaviour. The
operator list (`* <-> //`) can produce such crash mutants (e.g. float `//`). So
`score.py` splits kills into `assertion` / `crash` / `timeout`. `kill_rate` counts all
three (a killed mutant is killed); `assertion_kill_rate` is the honest headline and is
reported alongside it. This keeps the required operator set intact while making the
inflation visible instead of hidden.

## Golden cases live in each task's meta.yaml, not in one test file

The spec put ground truth inside `tests/test_corpus_sanity.py`. Instead each task
carries its own `golden_cases:` as data in `meta.yaml`, and the sanity test loads and
runs them all. This makes tasks self-contained (one folder = one task) and lets the
same cases drive `bench selfcheck` and the perfect-suite synthesizer without
duplication.

## No numpy/pandas/scipy in the required path

Built on Python 3.14, where compiled wheels are patchy. The scored path uses only
pydantic / pyyaml / typer / rich / openai (all install cleanly here). Stats use stdlib
`statistics`; `matplotlib` is imported lazily inside `report.py` and its absence
degrades to "no PNG" rather than an import error.

## Packaging: explicit package list

`[tool.setuptools] packages = ["llm_testgen_bench"]` — the flat layout (corpus/,
prompts/, results/ as siblings) otherwise trips setuptools' auto-discovery.
