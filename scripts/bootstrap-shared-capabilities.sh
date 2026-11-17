#!/usr/bin/env bash
set -euo pipefail

verify_only=false
[[ "${1:-}" == "--verify-only" ]] && verify_only=true
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

command -v openclaw >/dev/null || { echo 'OpenClaw CLI is unavailable.' >&2; exit 1; }
version="$(openclaw --version | grep -Eo '[0-9]{4}\.[0-9]+\.[0-9]+' | head -1)"
[[ -n "$version" ]] || { echo 'Unable to determine OpenClaw version.' >&2; exit 1; }
printf '%s\n%s\n' '2026.11.5' "$version" | sort -V -C || { echo "OpenClaw 2026.11.5 or newer is required; found $version." >&2; exit 1; }

gutsai_env=''
for name in GUTSAI_API_KEY; do [[ -n "${!name:-}" ]] && { gutsai_env="$name"; break; }; done
gemini_env=''
for name in GEMINI_API_KEY GOOGLE_API_KEY; do [[ -n "${!name:-}" ]] && { gemini_env="$name"; break; }; done
[[ -n "$gutsai_env" ]] && echo "GutsAI credential environment: $gutsai_env present" || echo 'GutsAI credential environment: missing'
[[ -n "$gemini_env" ]] && echo "Gemini credential environment: $gemini_env present" || echo 'Gemini credential environment: missing'

if $verify_only; then
  [[ -n "$gutsai_env" && -n "$gemini_env" ]] || exit 2
  openclaw config validate
  exit
fi

[[ -n "$gutsai_env" ]] || { echo 'Missing GUTSAI_API_KEY. Put it in the shell/Gateway environment, never this repository.' >&2; exit 1; }
[[ -n "$gemini_env" ]] || { echo 'Missing GEMINI_API_KEY or GOOGLE_API_KEY. Put it in the shell/Gateway environment, never this repository.' >&2; exit 1; }

batch_file="$(mktemp)"
trap 'rm -f "$batch_file"' EXIT
python3 - "$batch_file" <<'PY'
import json, sys
with open('capabilities/gutsai-provider.json', encoding='utf-8') as src:
    provider = json.load(src)
with open(sys.argv[1], 'w', encoding='utf-8') as dst:
    json.dump([{'path': 'models.providers.custom-api-gutsai-id', 'value': provider}], dst)
PY
openclaw config set --batch-file "$batch_file" --merge
openclaw config set models.providers.custom-api-gutsai-id.apiKey --ref-provider default --ref-source env --ref-id "$gutsai_env"
openclaw config set memory.search.provider gemini
openclaw config set memory.search.remote.apiKey --ref-provider default --ref-source env --ref-id "$gemini_env"
openclaw config validate
openclaw doctor --lint || echo 'WARNING: doctor --lint reported findings; review them before relying on this device.' >&2
echo 'Shared capability configuration applied. Start a new session (or restart the Gateway if requested by OpenClaw) to load it.'
