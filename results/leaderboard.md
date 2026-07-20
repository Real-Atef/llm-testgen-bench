# Leaderboard

Grading is mutation kill rate, not an LLM judge. `assert-kill` is the honest headline (mutants caught by a failing assertion); `kill` also counts mutants that merely crashed or timed out.

| model | valid% | mean kill | median kill | mean assert-kill | tokens/task | sec/task |
|---|---|---|---|---|---|---|
| llama3.1:8b | 28.6% | 0.274 | 0.000 | 0.274 | 640 | 68.2 |
| qwen2.5-coder:7b | 33.3% | 0.315 | 0.000 | 0.296 | 642 | 48.5 |
| qwen2.5:7b | 14.3% | 0.143 | 0.000 | 0.143 | 752 | 71.6 |

## Kill rate by failure class

| model | empty_and_none | float_precision | mutation_aliasing | off_by_one | ordering_stability | parsing_validation | unicode_text |
|---|---|---|---|---|---|---|---|
| llama3.1:8b | 0.583 | 0.000 | 0.333 | 0.000 | 0.000 | 0.333 | 0.667 |
| qwen2.5-coder:7b | 0.333 | 0.303 | 0.567 | 0.000 | 0.333 | 0.000 | 0.667 |
| qwen2.5:7b | 0.333 | 0.000 | 0.333 | 0.000 | 0.333 | 0.000 | 0.000 |
