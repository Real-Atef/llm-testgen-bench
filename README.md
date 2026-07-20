# llm-testgen-bench

Mutation-graded evaluation of LLM-generated test suites. No LLM judge — grading is
deterministic and adversarial: a model writes a pytest suite, the suite must pass
against the correct implementation, then we mutate the implementation and score the
model on **mutation kill rate**.

> Status: scaffold. Nothing below is implemented yet.

## Why

"Did the model write good tests?" is usually answered by another model. That is
circular and unfalsifiable. Mutation testing answers it with a number that cannot be
talked into a different value: how many deliberately broken implementations did the
generated suite catch?

## Quickstart

```bash
make setup
make test       # harness tests only, no model calls
make smoke      # 2 tasks x llama3.2:1b, needs Ollama
make run        # full matrix
```

## Corpus

21 pure functions, 3 per failure class:

| Failure class | Tasks | What it probes |
|---|---|---|
| `off_by_one` | t01–t03 | pagination, slicing, inclusive/exclusive bounds |
| `empty_and_none` | t04–t06 | empty list/str/dict, `None` handling |
| `unicode_text` | t07–t09 | casefold vs lower, combining chars, emoji length |
| `float_precision` | t10–t12 | accumulation, rounding, money in cents |
| `mutation_aliasing` | t13–t15 | functions that must not mutate their inputs |
| `ordering_stability` | t16–t18 | sort stability, tie-breaking, duplicate keys |
| `parsing_validation` | t19–t21 | semver, query strings, IPv4 |

Every `impl.py` is hand-reviewed and covered by hidden ground-truth cases in
`tests/test_corpus_sanity.py`, never shown to models.

## Mutation operators

<!-- TODO: fill from mutate.py once implemented -->

## Reproducibility

We do **not** claim determinism. `temperature=0` plus a seed does not give
byte-identical output through Ollama — batching, GPU scheduling, and version drift
all break it. Instead `make variance` re-runs the smoke matrix three times and
reports the spread in kill rate, so run-to-run noise is a measured quantity rather
than an assumption. See `tests/test_variance.py`.

## Threats to validity

- **Equivalent mutants.** Some mutants are semantically identical to the original and
  cannot be killed. They depress kill rate uniformly across models but inflate the
  apparent gap on small task counts.
- **Crash-kills vs assertion-kills.** A mutant that raises is trivially caught. These
  are tracked separately so kill rate is not inflated by mutants no suite could miss.
- **Small k.** Default `k=1`. Kill rate for a single sample is noisy; see the variance
  numbers before reading a leaderboard gap as real.
- **Model scale.** Results are for 7–8B local models. They do not transfer to frontier
  models without re-running.

## License

MIT
