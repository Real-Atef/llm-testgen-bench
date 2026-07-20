"""Aggregation and artifacts: results.json, leaderboard.md, kill_rates.png,
per-failure-class breakdown, and a variance summary for repeated runs."""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict
from pathlib import Path

from .config import settings
from .score import ScoreResult


# --------------------------------------------------------------------------- #
# raw persistence (makes runs resumable and `bench report` standalone)
# --------------------------------------------------------------------------- #
def raw_path(model: str, task_id: str, k_index: int, repeat: int = 0) -> Path:
    safe = model.replace(":", "_").replace("/", "_")
    return settings.raw_dir / f"{safe}__{task_id}__k{k_index}__r{repeat}.json"


def save_raw(result: ScoreResult, k_index: int, repeat: int = 0) -> Path:
    settings.ensure_dirs()
    p = raw_path(result.model, result.task_id, k_index, repeat)
    p.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def load_raw() -> list[ScoreResult]:
    results: list[ScoreResult] = []
    if not settings.raw_dir.exists():
        return results
    for f in sorted(settings.raw_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        data.pop("mutants", None)  # keep summary light; mutants stay on disk
        results.append(_from_summary(data))
    return results


def _from_summary(d: dict) -> ScoreResult:
    d = dict(d)
    d.setdefault("mutants", [])
    d["mutants"] = []
    return ScoreResult(**d)


# --------------------------------------------------------------------------- #
# aggregation
# --------------------------------------------------------------------------- #
def _mean(xs: list[float]) -> float:
    return statistics.fmean(xs) if xs else 0.0


def _median(xs: list[float]) -> float:
    return statistics.median(xs) if xs else 0.0


def summarize_model(results: list[ScoreResult]) -> dict:
    n = len(results)
    valid = [r for r in results if r.valid]
    kill_rates = [r.kill_rate for r in results]  # invalids contribute 0.0
    assertion_rates = [r.assertion_kill_rate for r in results]
    return {
        "n_tasks": n,
        "valid_pct": 100.0 * len(valid) / n if n else 0.0,
        "mean_kill_rate": _mean(kill_rates),
        "median_kill_rate": _median(kill_rates),
        "mean_assertion_kill_rate": _mean(assertion_rates),
        "mean_tokens_per_task": _mean([r.prompt_tokens + r.completion_tokens for r in results]),
        "mean_sec_per_task": _mean([r.wall_seconds for r in results]),
        "generation_errors": sum(1 for r in results if r.status == "generation_error"),
    }


def by_model(results: list[ScoreResult]) -> dict[str, list[ScoreResult]]:
    out: dict[str, list[ScoreResult]] = {}
    for r in results:
        out.setdefault(r.model, []).append(r)
    return out


# --------------------------------------------------------------------------- #
# markdown / json / png
# --------------------------------------------------------------------------- #
def _fmt(x: float, pct: bool = False) -> str:
    return f"{x:.1f}%" if pct else f"{x:.3f}"


def leaderboard_md(results: list[ScoreResult]) -> str:
    lines = [
        "# Leaderboard",
        "",
        "Grading is mutation kill rate, not an LLM judge. `assert-kill` is the "
        "honest headline (mutants caught by a failing assertion); `kill` also "
        "counts mutants that merely crashed or timed out.",
        "",
        "| model | valid% | mean kill | median kill | mean assert-kill | tokens/task | sec/task |",
        "|---|---|---|---|---|---|---|",
    ]
    for model, rs in sorted(by_model(results).items()):
        s = summarize_model(rs)
        lines.append(
            f"| {model} | {_fmt(s['valid_pct'], pct=True)} | "
            f"{_fmt(s['mean_kill_rate'])} | {_fmt(s['median_kill_rate'])} | "
            f"{_fmt(s['mean_assertion_kill_rate'])} | "
            f"{s['mean_tokens_per_task']:.0f} | {s['mean_sec_per_task']:.1f} |"
        )

    # per-failure-class breakdown (mean kill rate per class per model)
    classes = sorted({r.failure_class for r in results})
    lines += ["", "## Kill rate by failure class", "",
              "| model | " + " | ".join(classes) + " |",
              "|---|" + "|".join("---" for _ in classes) + "|"]
    for model, rs in sorted(by_model(results).items()):
        cells = []
        for c in classes:
            crs = [r.kill_rate for r in rs if r.failure_class == c]
            cells.append(_fmt(_mean(crs)) if crs else "-")
        lines.append(f"| {model} | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def write_reports(results: list[ScoreResult], results_dir: Path | None = None) -> dict[str, Path]:
    out = results_dir or settings.results_dir
    out.mkdir(parents=True, exist_ok=True)

    results_json = out / "results.json"
    results_json.write_text(
        json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lb = out / "leaderboard.md"
    lb.write_text(leaderboard_md(results), encoding="utf-8")

    png = out / "kill_rates.png"
    _write_png(results, png)

    return {"results_json": results_json, "leaderboard": lb, "png": png}


def _write_png(results: list[ScoreResult], path: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:  # pragma: no cover - matplotlib is optional at runtime
        return
    models, kills, asserts = [], [], []
    for model, rs in sorted(by_model(results).items()):
        s = summarize_model(rs)
        models.append(model)
        kills.append(s["mean_kill_rate"])
        asserts.append(s["mean_assertion_kill_rate"])
    if not models:
        return
    x = range(len(models))
    width = 0.38
    fig, ax = plt.subplots(figsize=(1.6 * len(models) + 3, 4))
    ax.bar([i - width / 2 for i in x], kills, width, label="kill rate")
    ax.bar([i + width / 2 for i in x], asserts, width, label="assert-kill rate")
    ax.set_xticks(list(x))
    ax.set_xticklabels(models, rotation=20, ha="right")
    ax.set_ylabel("mean rate")
    ax.set_ylim(0, 1)
    ax.set_title("Mutation kill rate by model")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# variance across repeated identical runs
# --------------------------------------------------------------------------- #
def variance_md(runs: list[list[ScoreResult]]) -> str:
    """Given N repeated runs of the same matrix, report per-model spread in
    mean kill rate. This is the measured stand-in for the determinism we do
    NOT claim."""
    lines = [
        "# Run-to-run variance",
        "",
        f"{len(runs)} identical repeats (temperature=0, seed=42). If output were "
        "truly deterministic these would be zero; they are not.",
        "",
        "| model | mean kill (per repeat) | spread (max-min) | stdev |",
        "|---|---|---|---|",
    ]
    models = sorted({r.model for run in runs for r in run})
    for model in models:
        per_repeat = []
        for run in runs:
            rs = [r for r in run if r.model == model]
            per_repeat.append(_mean([r.kill_rate for r in rs]))
        spread = (max(per_repeat) - min(per_repeat)) if per_repeat else 0.0
        sd = statistics.pstdev(per_repeat) if len(per_repeat) > 1 else 0.0
        vals = ", ".join(f"{v:.3f}" for v in per_repeat)
        lines.append(f"| {model} | {vals} | {spread:.3f} | {sd:.3f} |")
    lines.append("")
    return "\n".join(lines)
