#!/usr/bin/env python3
"""Capture honest GutsAI pricing/status snapshots and optional active uptime probes.

This records only data the public API actually exposes. It never treats catalog
status as proof of availability, and it never invents account quota or spend.
Requires GUTSAI_API_KEY. Reports go under ~/.openclaw/model-audits/ by default.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import time
import requests

BASE_URL = os.environ.get("GUTSAI_BASE_URL", "https://api.gutsai.id/v1").rstrip("/")
API_KEY = os.environ.get("GUTSAI_API_KEY")
if not API_KEY:
    raise SystemExit("GUTSAI_API_KEY is not set")

parser = argparse.ArgumentParser()
parser.add_argument("--probe-model", help="Make one tiny chat request to measure observed availability and latency")
parser.add_argument("--output", type=Path, help="Output JSON path")
args = parser.parse_args()

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
started = time.perf_counter()
response = session.get(f"{BASE_URL}/models", timeout=30)
models_latency = round(time.perf_counter() - started, 3)
response.raise_for_status()
rows = response.json().get("data", [])
models = [{
    "id": row.get("id"),
    "provider": row.get("provider"),
    "catalog_status": row.get("status"),
    "price_per_1m": row.get("price_per_1m"),
    "price_semantics": "provider catalog field; input/output split and currency unit are not exposed by this endpoint",
} for row in rows]

report = {
    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    "base_url": BASE_URL,
    "models_endpoint": {"http": response.status_code, "latency_s": models_latency, "count": len(models)},
    "models": models,
    "account_telemetry": {
        "quota": "unavailable: no supported endpoint",
        "balance": "unavailable: no supported endpoint",
        "provider_lifetime_spend": "unavailable: no supported endpoint",
        "rate_limit_headers": "not observed",
    },
    "scope": "OpenClaw can aggregate tokens/cost for requests it records; it cannot see usage made by other clients without a provider account endpoint.",
}

if args.probe_model:
    started = time.perf_counter()
    try:
        probe = session.post(
            f"{BASE_URL}/chat/completions",
            json={"model": args.probe_model, "messages": [{"role": "user", "content": "Reply only OK"}], "max_tokens": 8, "stream": False},
            timeout=60,
        )
        latency = round(time.perf_counter() - started, 3)
        body = probe.json()
        report["active_probe"] = {
            "model": args.probe_model,
            "http": probe.status_code,
            "ok": probe.status_code == 200,
            "latency_s": latency,
            "usage": body.get("usage") if probe.status_code == 200 else None,
            "error": body.get("error") if probe.status_code != 200 else None,
        }
    except requests.RequestException as exc:
        report["active_probe"] = {"model": args.probe_model, "ok": False, "error_type": type(exc).__name__}

output = args.output
if output is None:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path.home() / ".openclaw" / "model-audits" / f"gutsai-telemetry-{stamp}.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"REPORT={output}")
print(json.dumps({
    "models_http": report["models_endpoint"]["http"],
    "models": len(models),
    "active_probe": report.get("active_probe"),
    "quota": "unavailable",
    "provider_lifetime_spend": "unavailable",
}, ensure_ascii=False))
