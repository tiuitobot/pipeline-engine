#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" ]]; then
  echo "[ERROR] Not inside a git repository."
  exit 1
fi

SRC_HOOK="$REPO_ROOT/templates/commit-msg-gate.sh"
DST_HOOK="$REPO_ROOT/.git/hooks/commit-msg"

if [[ ! -f "$SRC_HOOK" ]]; then
  echo "[ERROR] Source hook not found: $SRC_HOOK"
  exit 1
fi

if [[ -f "$DST_HOOK" ]]; then
  read -r -p ".git/hooks/commit-msg already exists. Overwrite? (y/n) " ANSWER
  if [[ "$ANSWER" != "y" && "$ANSWER" != "Y" ]]; then
    echo "[ABORTED] Hook installation canceled."
    exit 0
  fi
fi

cp "$SRC_HOOK" "$DST_HOOK"
chmod +x "$DST_HOOK"

echo "[DONE] commit-msg hook installed at .git/hooks/commit-msg"
