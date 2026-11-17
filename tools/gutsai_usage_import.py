#!/usr/bin/env python3
"""Import GutsAI monthly usage CSV exports into one sanitized local history.

The output deliberately omits key_name and key_prefix. Provider-exported request
success is reported as success rate, never mislabeled as service uptime.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from collections import defaultdict

REQUIRED = {
    "date", "key_name", "key_prefix", "model", "requests", "failed_requests",
    "input_tokens", "cached_tokens", "output_tokens", "images", "cost_idr", "cost_usd",
}
INT_FIELDS = ("requests", "failed_requests", "input_tokens", "cached_tokens", "output_tokens", "images")
MONEY_FIELDS = ("cost_idr", "cost_usd")


def blank_totals() -> dict[str, int | Decimal]:
    return {**{name: 0 for name in INT_FIELDS}, **{name: Decimal("0") for name in MONEY_FIELDS}}


def add(target: dict, row: dict) -> None:
    for name in INT_FIELDS:
        target[name] += int(row[name] or 0)
    for name in MONEY_FIELDS:
        try:
            target[name] += Decimal(row[name] or "0")
        except InvalidOperation as exc:
            raise ValueError(f"Invalid {name}: {row[name]!r}") from exc


def finalize(values: dict) -> dict:
    result = {name: int(values[name]) for name in INT_FIELDS}
    result["cost_idr"] = int(values["cost_idr"])
    result["cost_usd"] = float(values["cost_usd"])
    requests = result["requests"]
    result["successful_requests"] = requests - result["failed_requests"]
    result["request_success_rate_pct"] = round(100 * result["successful_requests"] / requests, 4) if requests else None
    result["observed_tokens"] = result["input_tokens"] + result["output_tokens"]
    return result


parser = argparse.ArgumentParser()
parser.add_argument("csv", nargs="+", type=Path, help="Monthly GutsAI usage CSV exports")
parser.add_argument("--output", type=Path, default=Path.home() / ".openclaw" / "model-audits" / "gutsai-usage-history.json")
args = parser.parse_args()

paths = [path.resolve() for path in args.csv]
if len(paths) != len(set(paths)):
    raise SystemExit("Duplicate input path supplied; refusing to double-count it")

by_month: dict[str, dict] = defaultdict(blank_totals)
by_model: dict[str, dict] = defaultdict(blank_totals)
by_day: dict[str, dict] = defaultdict(blank_totals)
total = blank_totals()
source_files = []
row_count = 0
first_date = None
last_date = None

for path in paths:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or []) != REQUIRED:
            missing = sorted(REQUIRED - set(reader.fieldnames or []))
            extra = sorted(set(reader.fieldnames or []) - REQUIRED)
            raise SystemExit(f"Unexpected schema in {path.name}; missing={missing}, extra={extra}")
        file_rows = 0
        for row in reader:
            day = dt.date.fromisoformat(row["date"])
            month = day.strftime("%Y-%m")
            model = row["model"].strip()
            if not model:
                raise SystemExit(f"Blank model in {path.name}")
            add(total, row)
            add(by_month[month], row)
            add(by_model[model], row)
            add(by_day[day.isoformat()], row)
            first_date = day if first_date is None or day < first_date else first_date
            last_date = day if last_date is None or day > last_date else last_date
            file_rows += 1
            row_count += 1
        source_files.append({"name": path.name, "rows": file_rows})

report = {
    "schema_version": 1,
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "scope": "Provider-exported usage contained in the supplied CSV files; may include clients other than OpenClaw.",
    "privacy": "key_name and key_prefix are intentionally omitted",
    "availability_semantics": "request_success_rate_pct is observed request success, not uptime or an SLA",
    "token_semantics": "observed_tokens is input_tokens + output_tokens; cached_tokens is retained separately and not added again",
    "period": {"first_activity": first_date.isoformat() if first_date else None, "last_activity": last_date.isoformat() if last_date else None},
    "source_files": source_files,
    "rows": row_count,
    "totals": finalize(total),
    "by_month": {key: finalize(value) for key, value in sorted(by_month.items())},
    "by_model": dict(sorted(((key, finalize(value)) for key, value in by_model.items()), key=lambda item: item[1]["cost_idr"], reverse=True)),
    "by_day": {key: finalize(value) for key, value in sorted(by_day.items())},
    "unavailable": {
        "quota": "not present in exports or supported API endpoints",
        "balance": "not present in exports or supported API endpoints",
        "service_uptime": "monthly exports contain request outcomes, not continuous uptime observations",
    },
}

args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"REPORT={args.output}")
print(json.dumps({"period": report["period"], "rows": row_count, **report["totals"]}, ensure_ascii=False))
