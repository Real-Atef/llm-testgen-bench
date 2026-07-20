"""Central configuration. Values may be overridden via environment variables
prefixed with ``BENCH_`` (e.g. ``BENCH_OLLAMA_BASE_URL``)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root = parent of this package directory.
REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BENCH_", extra="ignore")

    # --- Ollama / inference -------------------------------------------------
    ollama_base_url: str = "http://localhost:11434/v1"
    api_key: str = "ollama"  # Ollama ignores it, but the openai client requires one.
    temperature: float = 0.0
    seed: int = 42
    request_timeout: float = 120.0
    max_retries: int = 3

    # --- Run matrix ---------------------------------------------------------
    default_models: list[str] = Field(
        default_factory=lambda: ["qwen2.5-coder:7b", "llama3.1:8b", "qwen2.5:7b"]
    )
    # Smoke uses whatever tiny model is actually pulled locally. llama3.2 (3B)
    # is the documented default; override with BENCH_SMOKE_MODEL.
    smoke_model: str = "llama3.2"
    k: int = 1

    # --- Mutation / sandbox -------------------------------------------------
    max_mutants: int = 30
    sandbox_timeout: float = 60.0
    mutant_timeout: float = 30.0

    # --- Paths --------------------------------------------------------------
    corpus_dir: Path = REPO_ROOT / "corpus" / "tasks"
    prompts_dir: Path = REPO_ROOT / "prompts"
    results_dir: Path = REPO_ROOT / "results"
    raw_dir: Path = REPO_ROOT / "results" / "raw"
    cache_dir: Path = REPO_ROOT / ".bench_cache"

    def ensure_dirs(self) -> None:
        for d in (self.results_dir, self.raw_dir, self.cache_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
