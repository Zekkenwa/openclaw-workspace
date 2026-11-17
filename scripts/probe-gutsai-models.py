#!/usr/bin/env python3
"""Live-probe every Guts AI advertised model without printing credentials.

Requires GUTSAI_API_KEY. Writes a timestamped JSON report under
~/.openclaw/model-audits/. Discovery rows are never treated as proof of chat
availability: every model is tested through /v1/chat/completions.
"""
from __future__ import annotations
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

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
rows = session.get(f"{BASE_URL}/models", timeout=30).json().get("data", [])
transient_http = {408, 429, 500, 502, 503, 504}
transient_words = ("offline", "maintenance", "temporarily unavailable", "capacity", "quota", "rate limit", "overloaded", "run out")
permanent_words = ("not found", "unknown model", "does not exist", "unsupported model", "image-only", "not support chat")
results = []

for index, row in enumerate(rows, 1):
    model_id = row.get("id")
    record = {
        "id": model_id,
        "advertised_status": row.get("status"),
        "supports_vision": row.get("supports_vision"),
        "input_modalities": row.get("input_modalities"),
    }
    for attempt in (1, 2):
        started = time.perf_counter()
        try:
            response = session.post(
                f"{BASE_URL}/chat/completions",
                json={"model": model_id, "messages": [{"role": "user", "content": "Reply with exactly: OK"}], "max_tokens": 8, "temperature": 0},
                timeout=45,
            )
            body = response.text[:800]
            lowered = body.lower()
            record.update({
                "http": response.status_code,
                "latency_s": round(time.perf_counter() - started, 3),
                "error_excerpt": None if response.status_code == 200 else body[:300],
            })
            if response.status_code == 200 and not any(word in lowered for word in transient_words):
                record["class"] = "online"
                break
            if response.status_code in transient_http or any(word in lowered for word in transient_words):
                record["class"] = "transient"
                if attempt == 1:
                    retry_after = min(int(response.headers.get("Retry-After", "5") or 5), 30)
                    time.sleep(max(retry_after, 5))
                    continue
                break
            record["class"] = "unusable" if any(word in lowered for word in permanent_words) or response.status_code in {400, 404, 405, 422} else "unusable"
            break
        except requests.RequestException as exc:
            record.update({"http": None, "latency_s": round(time.perf_counter() - started, 3), "error_excerpt": str(exc)[:300], "class": "transient"})
            if attempt == 1:
                time.sleep(5)
                continue
    print(f"[{index}/{len(rows)}] {model_id}: {record['class']} ({record.get('http')}, advertised={record.get('advertised_status')})", flush=True)
    results.append(record)
    time.sleep(0.35)

stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
report_dir = Path.home() / ".openclaw" / "model-audits"
report_dir.mkdir(parents=True, exist_ok=True)
report_path = report_dir / f"gutsai-model-audit-{stamp}.json"
report = {"timestamp": dt.datetime.now(dt.timezone.utc).isoformat(), "advertised_count": len(rows), "results": results}
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
counts = {kind: sum(item["class"] == kind for item in results) for kind in ("online", "transient", "unusable")}
print(f"REPORT={report_path}")
print(json.dumps(counts))
