# llm-testgen-bench

**How good are the pytest suites that local LLMs write?** — graded not by an LLM
judge but by **mutation testing**. For each task a model generates a test suite; the
suite must first pass against the correct implementation (or it is *invalid*); then
the harness generates single-mutation variants of that implementation and scores the
suite on how many it catches. The score — mutation **kill rate** — is deterministic,
adversarial, and judge-free: it cannot be talked into a different value.

## Methodology

A good test suite fails when the code under test is wrong. So we break the code, on
purpose, one edit at a time (swap a `<` for `<=`, an `and` for an `or`, bump a
constant) and ask: did the suite notice? A suite that catches 9 of 10 mutants is
measurably better than one that catches 2 — no rubric, no judge, no vibes. The only
LLM in the loop is the one *writing the tests*; the grading is pure AST manipulation
and subprocess pytest runs.

## Quickstart

```bash
make setup                 # venv + install + freeze lockfile
make test                  # 95 harness tests, no model calls
make smoke                 # 2 tasks x llama3.2 (needs Ollama) -> leaderboard + PNG
make run                   # full matrix (edit models to ones you've pulled)
```

No Make? Use `python verify.py` (test + smoke) and `python -m llm_testgen_bench.cli …`.

## What a run produces

`results/leaderboard.md` (committed), `results/results.json` (full per-mutant detail
incl. tokens + wall-time), and `results/kill_rates.png`.

### Actual smoke result (llama3.2, 3B, CPU)

```
| model    | valid% | mean kill | median kill | mean assert-kill | tokens/task | sec/task |
| llama3.2 |   0.0% |     0.000 |       0.000 |            0.000 |         515 |     29.4 |
```

That 0% is the finding, not a bug. On both of the two easiest tasks, the 3B model
wrote a pytest file that **fails against the correct implementation** — it called
`chunk([])` without the required `size` argument, and it asserted that
`first_non_empty([""])` returns `""` when the documented contract skips blank strings.
A suite that doesn't pass on correct code is unusable, so it scores zero. *"Small local
models can't reliably produce a self-consistent test file"* is a more honest, more
interesting write-up than a leaderboard of near-identical numbers. Pull `qwen2.5-coder`
and the picture changes — that's the experiment.

## Mutation operators (backend: `pymutant`, pure stdlib)

| Category | Mutation |
|---|---|
| comparison | `<`↔`<=`, `>`↔`>=`, `==`↔`!=` |
| arithmetic | `+`↔`-`, `*`↔`//` |
| boolean | `and`↔`or`, `not X`→`X` |
| constant | int `n`→`n+1`, `True`↔`False` |
| boundary | slice/`range` int arg `n`→`n+1` (a labelled subset of the constant op) |
| return | `return X`→`return None` |

Each mutant applies exactly one mutation to a fresh AST copy. Mutants are produced in
deterministic walk order, deduplicated by unparsed source (this drops most equivalent
mutants), only kept if they compile, and capped at 30 per task.

## Corpus taxonomy

21 pure functions, 3 per failure class. Every `impl.py` is hand-written, reviewed, and
covered by golden cases in its own `meta.yaml` (the harness's hidden ground truth,
verified by `tests/test_corpus_sanity.py` and never shown to models).

| Failure class | Tasks | Probes |
|---|---|---|
| `off_by_one` | t01–t03 | pagination, chunking, half-open interval overlap |
| `empty_and_none` | t04–t06 | last-index sentinel, blank-skipping, middle truncation |
| `unicode_text` | t07–t09 | casefold dedupe, combining-mark length, word counting |
| `float_precision` | t10–t12 | dollars→cents, exact remainder split, half-up tax |
| `mutation_aliasing` | t13–t15 | sort/rotate/dedupe that must not mutate the input |
| `ordering_stability` | t16–t18 | competition ranking, stable grouping, stable top-N |
| `parsing_validation` | t19–t21 | semver compare, query-string parse, IPv4 validate |

## Reproducibility

This project does **not** claim determinism. `temperature=0` + `seed=42` does not yield
byte-identical output through Ollama (the OpenAI-compatible endpoint doesn't reliably
honor `seed`; batching and GPU scheduling add noise). Instead:

```bash
bench run --smoke --repeat 3   # fresh samples (auto --no-cache), then:
bench variance                 # results/variance.md: per-model spread in kill rate
```

Run-to-run spread is a *measured* number. On single-request CPU decoding it is often
~0 (a legitimate result); on GPU it usually is not.

## How to add a task

1. `mkdir corpus/tasks/t22_myfeature/`
2. Write `impl.py` — one public function with a docstring **contract**, containing
   ≥4 mutable operators from the table above.
3. Write `meta.yaml` — `id, title, difficulty(1-3), failure_class, entrypoint,
   description, golden_cases` (≥3 hand-verified cases; each is `args`/`kwargs` with
   `expected:` or `raises:`).
4. `bench validate` (checks schema + operator count) and `make test` (runs golden
   cases). Green means the ground truth holds.

## How to add a model

Pull it (`ollama pull <model>`) and pass it: `bench run --models <model>,…`. The smoke
model is `BENCH_SMOKE_MODEL` (default `llama3.2`). Any Ollama model exposed on the
OpenAI-compatible endpoint works; no code change needed.

## Threats to validity

- **Equivalent mutants.** Some single mutations don't change behaviour and can't be
  killed. Dedup-by-source removes many; the rest depress kill rate uniformly and matter
  more at small task counts.
- **Crash-kills vs assertion-kills.** A mutant that merely errors is caught by any
  running suite. These are counted separately; `assertion_kill_rate` is the honest
  headline. See `DECISIONS.md`.
- **Whole-suite validity is strict.** One buggy test invalidates the entire suite
  (kill rate 0). This is deliberate — an unusable suite deserves zero — but it makes the
  benchmark harsh on weak models, as the smoke result shows.
- **Small k, local-model variance.** Default `k=1`; a single sample is noisy. Read
  `bench variance` before treating a leaderboard gap as real.
- **Ground-truth risk.** Every number rests on the corpus being correct. It is verified
  by execution (golden cases) and by an independent adversarial audit, but a corpus this
  small should still be read by a human before you cite results from it.

## Layout

```
llm_testgen_bench/   config, ollama_client, corpus, generate, sandbox,
                     mutate, score, report, cli, testing
corpus/tasks/        t01..t21 — impl.py + meta.yaml (with golden_cases)
prompts/             generate_tests.txt
tests/               95 harness tests (corpus sanity, mutate, sandbox,
                     extraction, score, variance)
results/             leaderboard.md (committed) + gitignored run artifacts
```

## License

MIT
