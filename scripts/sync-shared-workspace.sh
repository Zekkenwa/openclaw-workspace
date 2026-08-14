#!/usr/bin/env bash
# Safe Git synchronization for the shared OpenClaw workspace.
set -euo pipefail

mode="status"
message="Sync shared OpenClaw workspace"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) mode="$2"; shift 2 ;;
    --message) message="$2"; shift 2 ;;
    -h|--help)
      printf 'Usage: %s --mode start|push|status [--message "commit message"]\n' "$0"
      exit 0
      ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 64 ;;
  esac
done

case "$mode" in start|push|status) ;; *) printf 'Invalid mode: %s\n' "$mode" >&2; exit 64 ;; esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

shared_paths=(
  .gitignore AGENTS.md HEARTBEAT.md IDENTITY.md MEMORY.md SOUL.md TOOLS.md USER.md
  memory skills scripts
)

shared_changes() {
  git status --porcelain -- "${shared_paths[@]}"
}

case "$mode" in
  status)
    git status --short --branch
    if [[ -z "$(shared_changes)" ]]; then
      echo 'No uncommitted shared-workspace changes.'
    else
      shared_changes
    fi
    ;;

  start)
    if [[ -n "$(shared_changes)" ]]; then
      echo 'Shared files have local changes. Not pulling, to avoid overwriting or creating a conflict. Run push mode first.' >&2
      shared_changes >&2
      exit 2
    fi

    git fetch origin
    read -r ahead behind < <(git rev-list --left-right --count 'HEAD...@{upstream}')
    if (( ahead > 0 )); then
      echo "Local branch is $ahead commit(s) ahead of origin. Push it before starting a session." >&2
      exit 2
    elif (( behind > 0 )); then
      git pull --ff-only origin main
      echo "Pulled $behind commit(s) from origin/main."
    else
      echo 'Already up to date with origin/main.'
    fi
    ;;

  push)
    if [[ -z "$(shared_changes)" ]]; then
      echo 'No shared-workspace changes to commit or push.'
      exit 0
    fi

    existing_paths=()
    for path in "${shared_paths[@]}"; do
      [[ -e "$path" ]] && existing_paths+=("$path")
    done
    git add -- "${existing_paths[@]}"
    if git diff --cached --quiet; then
      echo 'No staged shared-workspace changes to commit or push.'
      exit 0
    fi
    git commit -m "$message"
    git push origin main
    echo 'Committed and pushed shared-workspace changes.'
    ;;
esac
