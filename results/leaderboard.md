# Leaderboard

Grading is mutation kill rate, not an LLM judge. `assert-kill` is the honest headline (mutants caught by a failing assertion); `kill` also counts mutants that merely crashed or timed out.

| model | valid% | mean kill | median kill | mean assert-kill | tokens/task | sec/task |
|---|---|---|---|---|---|---|
| llama3.2 | 0.0% | 0.000 | 0.000 | 0.000 | 515 | 29.4 |

## Kill rate by failure class

| model | empty_and_none | off_by_one |
|---|---|---|
| llama3.2 | 0.000 | 0.000 |
