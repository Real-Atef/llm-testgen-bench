"""Thin, cached wrapper over the Ollama OpenAI-compatible chat endpoint.

Design notes
------------
* Every real model call goes through :class:`OllamaClient`. Tests inject a
  stub with the same ``chat`` signature, so no test needs a running server.
* Responses are cached on disk keyed by ``sha256(model + messages + params)``.
  The cache makes the whole benchmark resumable and keeps re-runs free.
* We pass ``temperature=0`` and ``seed`` as a *best effort* toward stable
  output. We do NOT claim byte-identical determinism — see ``bench variance``
  and README > Reproducibility for why that claim would be false.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from .config import settings


@dataclass
class ChatResult:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    wall_seconds: float
    cached: bool


class ChatBackend(Protocol):
    """Anything the harness can generate from. Real backend or a test stub."""

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        seed: int = 42,
    ) -> ChatResult: ...


def _cache_key(model: str, messages: list[dict[str, str]], params: dict[str, Any]) -> str:
    payload = json.dumps(
        {"model": model, "messages": messages, "params": params},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class OllamaClient:
    """Real backend. Lazily constructs the ``openai`` client so that importing
    this module never requires the dependency or a live server."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 cache_dir: Path | None = None, use_cache: bool = True):
        self.base_url = base_url or settings.ollama_base_url
        self.api_key = api_key or settings.api_key
        self.cache_dir = cache_dir or settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_cache = use_cache
        self._client = None

    def _openai(self):
        if self._client is None:
            from openai import OpenAI  # imported lazily on first real call

            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=settings.request_timeout,
                max_retries=0,  # we do our own backoff below
            )
        return self._client

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        seed: int = 42,
    ) -> ChatResult:
        params = {"temperature": temperature, "seed": seed}
        key = _cache_key(model, messages, params)
        cache_path = self._cache_path(key)

        if self.use_cache and cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            data["cached"] = True
            return ChatResult(**data)

        last_err: Exception | None = None
        for attempt in range(settings.max_retries):
            try:
                start = time.perf_counter()
                resp = self._openai().chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    seed=seed,
                )
                wall = time.perf_counter() - start
                choice = resp.choices[0]
                usage = resp.usage
                result = ChatResult(
                    text=choice.message.content or "",
                    model=model,
                    prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                    wall_seconds=wall,
                    cached=False,
                )
                if self.use_cache:
                    payload = asdict(result)
                    cache_path.write_text(
                        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
                    )
                return result
            except Exception as exc:  # noqa: BLE001 - surface after retries
                last_err = exc
                time.sleep(2**attempt)  # 1s, 2s, 4s

        raise RuntimeError(
            f"Ollama call failed after {settings.max_retries} attempts for "
            f"model={model!r}: {last_err}"
        )
