"""`bench` command-line interface."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from .config import settings
from .corpus import load_tasks, get_task
from .generate import extract_code  # noqa: F401  (kept for parity/debugging)
from .mutate import default_backend
from .ollama_client import OllamaClient
from .report import load_raw, save_raw, write_reports, variance_md
from .score import score_task
from .testing import StubClient, synth_suite_from_golden, fenced

app = typer.Typer(add_completion=False, help="Mutation-graded LLM test-suite benchmark.")
console = Console()


def _select_tasks(spec: str):
    tasks = load_tasks()
    if spec == "all":
        return tasks
    n = int(spec)
    return tasks[:n]


def _smoke_tasks(n: int = 2):
    """The n easiest tasks: difficulty 1, fewest mutation sites."""
    tasks = load_tasks()
    d1 = [t for t in tasks if t.difficulty == 1] or tasks
    d1.sort(key=lambda t: default_backend.count_mutable_operators(t.impl_source()))
    return d1[:n]


@app.command()
def run(
    models: str = typer.Option(None, help="Comma-separated model list."),
    tasks: str = typer.Option("all", help="'all' or an integer count."),
    k: int = typer.Option(None, help="Samples per (model, task)."),
    smoke: bool = typer.Option(False, help="2 easiest tasks x the smoke model."),
    repeat: int = typer.Option(1, help="Repeat the whole matrix N times (variance)."),
    resume: bool = typer.Option(True, help="Skip (model,task,k,repeat) already on disk."),
    no_cache: bool = typer.Option(False, help="Bypass the response cache (fresh calls)."),
):
    """Run the benchmark and write results/leaderboard.md + kill_rates.png."""
    settings.ensure_dirs()
    # Variance is only meaningful with fresh samples: the cache would make every
    # repeat identical. So repeated runs bypass the cache automatically.
    if repeat > 1:
        no_cache = True
        console.print("[dim]repeat>1: bypassing response cache to sample fresh outputs[/]")
    if smoke:
        model_list = [settings.smoke_model]
        task_list = _smoke_tasks(2)
        k = 1
    else:
        model_list = [m.strip() for m in (models or ",".join(settings.default_models)).split(",") if m.strip()]
        task_list = _select_tasks(tasks)
        k = k or settings.k

    client = OllamaClient(use_cache=not no_cache)
    all_results = []
    for rep in range(repeat):
        for model in model_list:
            for task in task_list:
                for ki in range(k):
                    existing = load_existing(model, task.id, ki, rep)
                    if resume and existing is not None:
                        console.print(f"[dim]skip[/] {model} {task.id} k{ki} r{rep}")
                        all_results.append(existing)
                        continue
                    console.print(f"[cyan]run[/]  {model} {task.id} k{ki} r{rep}")
                    res = score_task(client, model, task)
                    save_raw(res, ki, rep)
                    all_results.append(res)

    paths = write_reports(load_raw())
    console.print(f"[green]wrote[/] {paths['leaderboard']}")


def load_existing(model, task_id, ki, rep):
    from .report import raw_path
    import json
    p = raw_path(model, task_id, ki, rep)
    if not p.exists():
        return None
    from .report import _from_summary
    return _from_summary(json.loads(p.read_text(encoding="utf-8")))


@app.command()
def report():
    """Re-render leaderboard + chart from results/raw/."""
    results = load_raw()
    if not results:
        console.print("[yellow]no raw results found; run `bench run` first[/]")
        raise typer.Exit(1)
    paths = write_reports(results)
    console.print(f"[green]wrote[/] {paths['leaderboard']}  and  {paths['png']}")


@app.command()
def variance():
    """Summarize run-to-run spread across repeats already on disk."""
    import json
    from .report import _from_summary

    runs: dict[int, list] = {}
    for f in sorted(settings.raw_dir.glob("*__r*.json")):
        rep = int(f.stem.split("__r")[-1])
        runs.setdefault(rep, []).append(_from_summary(json.loads(f.read_text(encoding="utf-8"))))
    if len(runs) < 2:
        console.print("[yellow]need >=2 repeats; run `bench run --smoke --repeat 3`[/]")
        raise typer.Exit(1)
    out = settings.results_dir / "variance.md"
    out.write_text(variance_md([runs[k] for k in sorted(runs)]), encoding="utf-8")
    console.print(f"[green]wrote[/] {out}")


@app.command()
def validate():
    """Validate every task's meta.yaml and impl."""
    tasks = load_tasks()
    for t in tasks:
        n = default_backend.count_mutable_operators(t.impl_source())
        flag = "" if n >= 4 else "  [red]<4 mutable ops![/]"
        console.print(f"[green]ok[/] {t.id}  ({t.failure_class}, {n} sites){flag}")
    console.print(f"[bold]{len(tasks)} tasks valid[/]")


@app.command()
def selfcheck():
    """(a) stub end-to-end, no Ollama; (b) one real smoke-model generation."""
    task = load_tasks()[0]

    # (a) deterministic pipeline check with a synthesized perfect suite.
    stub = StubClient(fenced(synth_suite_from_golden(task)))
    res = score_task(stub, "stub", task)
    assert res.valid, f"stub suite should be valid, got {res.invalid_reason}"
    assert res.total_mutants > 0, "expected mutants for task #1"
    assert res.kill_rate > 0.0, "perfect suite should kill mutants"
    console.print(f"[green](a) stub end-to-end OK[/] kill_rate={res.kill_rate:.2f} "
                  f"on {task.id} ({res.total_mutants} mutants)")

    # (b) one real generation on the smoke model.
    client = OllamaClient()
    real = score_task(client, settings.smoke_model, task)
    console.print(f"[green](b) real {settings.smoke_model} OK[/] status={real.status} "
                  f"valid={real.valid} kill_rate={real.kill_rate:.2f}")

    console.print("[bold green]SELFCHECK PASSED[/]")


if __name__ == "__main__":
    app()
