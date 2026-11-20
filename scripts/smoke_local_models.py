#!/usr/bin/env python3
"""Smoke-test and benchmark the local Ollama model suite.

Runs one fixed compliance-extraction prompt against every model in the suite,
checks that each answers with valid JSON in the expected shape, and writes a
Markdown benchmark log. Standard library only, so it runs with a plain
``python3`` and no project install:

    python3 scripts/smoke_local_models.py
    python3 scripts/smoke_local_models.py --models qwen2.5:3b,gemma2:2b --runs 3

Exit code is 0 only when every model passed. A model counts as "run" for the
submission only if it passed here and the log is committed.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_SUITE = ["qwen2.5:3b", "llama3.2:3b", "deepseek-r1:1.5b", "gemma2:2b"]
REPO_ROOT = Path(__file__).resolve().parents[1]

SYSTEM_PROMPT = (
    "You are a compliance analyst for a Bangladeshi garment exporter. "
    "Read the regulatory notice and answer with one JSON object only, with keys: "
    '"summary" (string), "jurisdiction" (string), '
    '"severity" (one of "low", "medium", "high", "critical"), and '
    '"obligations" (array of objects with "action" and "deadline" strings). '
    "Do not add any text outside the JSON."
)

USER_PROMPT = (
    "NOTICE (fictional test fixture): From 1 March 2027, importers placing cotton "
    "garments on the EU market must hold a due-diligence statement tracing the cotton "
    "to its country of harvest. Suppliers must provide spinning-mill invoices and "
    "ginning certificates for every shipment. Shipments without a statement will be "
    "held at the border. Buyers expect supplier evidence 60 days before shipment."
)

REQUIRED_KEYS = {"summary", "jurisdiction", "severity", "obligations"}
SEVERITIES = {"low", "medium", "high", "critical"}
_THINK_RE = re.compile(r"<think>(.*?)</think>", flags=re.DOTALL | re.IGNORECASE)


@dataclass
class RunResult:
    latency_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    eval_seconds: float = 0.0
    reasoning_chars: int = 0
    json_valid: bool = False
    schema_valid: bool = False
    error: str = ""


@dataclass
class ModelReport:
    model: str
    installed: bool
    runs: list[RunResult] = field(default_factory=list)
    error: str = ""

    @property
    def passed(self) -> bool:
        return self.installed and bool(self.runs) and all(r.schema_valid for r in self.runs)


def normalise(model: str) -> str:
    """Accept ``ollama/qwen2.5:3b`` or ``qwen2.5:3b``; Ollama wants the bare tag."""
    model = model.strip()
    for prefix in ("ollama_chat/", "ollama/"):
        if model.startswith(prefix):
            return model[len(prefix) :]
    return model


def _tag_matches(wanted: str, installed: set[str]) -> bool:
    if wanted in installed:
        return True
    return ":" not in wanted and f"{wanted}:latest" in installed


def split_reasoning(text: str) -> tuple[str, str]:
    reasoning = "\n".join(p.strip() for p in _THINK_RE.findall(text))
    answer = _THINK_RE.sub("", text)
    if "<think>" in answer.lower():
        start = answer.lower().index("<think>")
        reasoning = "\n".join(filter(None, [reasoning, answer[start + 7 :].strip()]))
        answer = answer[:start]
    answer = re.sub(r"^```(?:json)?\s*|\s*```$", "", answer.strip(), flags=re.IGNORECASE)
    return answer.strip(), reasoning


def validate(payload: Any) -> bool:
    if not isinstance(payload, dict) or not payload.keys() >= REQUIRED_KEYS:
        return False
    if str(payload["severity"]).lower() not in SEVERITIES:
        return False
    obligations = payload["obligations"]
    return (
        isinstance(obligations, list)
        and len(obligations) > 0
        and all(isinstance(o, dict) and "action" in o for o in obligations)
    )


def _request(base_url: str, path: str, body: dict | None, timeout: float) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(  # noqa: S310 - local runtime URL
        base_url.rstrip("/") + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - local runtime URL
        return json.loads(resp.read().decode())


def installed_models(base_url: str, timeout: float) -> set[str]:
    tags = _request(base_url, "/api/tags", None, timeout)
    return {m.get("name") or m.get("model", "") for m in tags.get("models", [])}


def ollama_version(base_url: str, timeout: float) -> str:
    try:
        return str(_request(base_url, "/api/version", None, timeout).get("version", "unknown"))
    except (urllib.error.URLError, OSError, ValueError):
        return "unknown"


def run_once(base_url: str, model: str, timeout: float) -> RunResult:
    body = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
    }
    started = time.perf_counter()
    try:
        response = _request(base_url, "/api/chat", body, timeout)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return RunResult(
            latency_ms=int((time.perf_counter() - started) * 1000),
            error=f"{type(exc).__name__}: {exc}",
        )
    latency_ms = int((time.perf_counter() - started) * 1000)
    message = response.get("message") or {}
    content = message.get("content") or ""
    answer, reasoning = split_reasoning(content)
    thinking = message.get("thinking")
    if isinstance(thinking, str) and thinking.strip():
        reasoning = "\n".join(filter(None, [thinking.strip(), reasoning]))
    result = RunResult(
        latency_ms=latency_ms,
        prompt_tokens=int(response.get("prompt_eval_count") or 0),
        completion_tokens=int(response.get("eval_count") or 0),
        eval_seconds=(response.get("eval_duration") or 0) / 1e9,
        reasoning_chars=len(reasoning),
    )
    try:
        parsed = json.loads(answer)
    except json.JSONDecodeError as exc:
        result.error = f"invalid JSON: {exc.msg}"
        return result
    result.json_valid = True
    result.schema_valid = validate(parsed)
    if not result.schema_valid:
        result.error = "JSON missing required keys or values"
    return result


def benchmark(base_url: str, models: list[str], runs: int, timeout: float) -> list[ModelReport]:
    try:
        installed = installed_models(base_url, timeout)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise SystemExit(
            f"Cannot reach Ollama at {base_url} ({exc}). Start it with `ollama serve`."
        ) from exc
    reports: list[ModelReport] = []
    for model in models:
        if not _tag_matches(model, installed):
            reports.append(
                ModelReport(model, installed=False, error=f"not pulled (ollama pull {model})")
            )
            continue
        report = ModelReport(model, installed=True)
        for _ in range(runs):
            report.runs.append(run_once(base_url, model, timeout))
        reports.append(report)
    return reports


def _median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def render_markdown(reports: list[ModelReport], *, base_url: str, version: str, runs: int) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    passed = sum(r.passed for r in reports)
    lines = [
        "# Local model smoke benchmark",
        "",
        f"- Date: {now}",
        f"- Ollama: {version} at `{base_url}`",
        f"- Host: {platform.system()} {platform.machine()}, Python {platform.python_version()}",
        f"- Runs per model: {runs}; prompt: fixed compliance extraction (JSON mode)",
        f"- Result: **{passed}/{len(reports)} models passed**",
        "",
        "| Model | Pulled | Passed | Median latency (ms) | Prompt tok | Completion tok "
        "| Tok/s | Valid JSON | Schema OK | Reasoning chars | Note |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in reports:
        if not r.runs:
            lines.append(
                f"| `{r.model}` | {'yes' if r.installed else 'no'} | no "
                f"| - | - | - | - | - | - | - | {r.error} |"
            )
            continue
        tok_s = [x.completion_tokens / x.eval_seconds for x in r.runs if x.eval_seconds]
        errors = sorted({x.error for x in r.runs if x.error})
        lines.append(
            f"| `{r.model}` | yes | {'yes' if r.passed else 'no'} "
            f"| {_median([x.latency_ms for x in r.runs]):.0f} "
            f"| {_median([x.prompt_tokens for x in r.runs]):.0f} "
            f"| {_median([x.completion_tokens for x in r.runs]):.0f} "
            f"| {_median(tok_s):.1f} "
            f"| {sum(x.json_valid for x in r.runs)}/{len(r.runs)} "
            f"| {sum(x.schema_valid for x in r.runs)}/{len(r.runs)} "
            f"| {_median([x.reasoning_chars for x in r.runs]):.0f} "
            f"| {'; '.join(errors)} |"
        )
    lines += [
        "",
        "Generated by `scripts/smoke_local_models.py`. Latency includes model load on the "
        "first run; it is a smoke measurement on this machine, not a quality benchmark.",
        "",
    ]
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    env_suite = os.environ.get("OLLAMA_MODEL_SUITE", "")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--base-url", default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    parser.add_argument(
        "--models",
        default=env_suite or ",".join(DEFAULT_SUITE),
        help="Comma-separated Ollama tags (ollama/ prefix optional)",
    )
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=180.0, help="Seconds per request")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Markdown log path (default docs/benchmarks/local_models_<date>.md)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    models = [normalise(m) for m in args.models.split(",") if m.strip()]
    reports = benchmark(args.base_url, models, max(1, args.runs), args.timeout)
    markdown = render_markdown(
        reports,
        base_url=args.base_url,
        version=ollama_version(args.base_url, args.timeout),
        runs=max(1, args.runs),
    )
    out = args.out or (
        REPO_ROOT
        / "docs"
        / "benchmarks"
        / f"local_models_{datetime.now(UTC).strftime('%Y%m%d_%H%M')}.md"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"Wrote {out}")
    return 0 if all(r.passed for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
