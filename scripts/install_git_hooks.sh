#!/usr/bin/env bash
# install_git_hooks.sh — instala hooks versionados e configura core.hooksPath
# Rodar uma vez após git clone ou git init.
# P139: hooks versionados em .githooks/ garantem persistência entre clones.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" ]]; then
  echo "[ERROR] Not inside a git repository."
  exit 1
fi

GITHOOKS_DIR="$REPO_ROOT/.githooks"

if [[ ! -d "$GITHOOKS_DIR" ]]; then
  echo "[ERROR] .githooks/ não encontrado em $REPO_ROOT"
  echo "  Certifique-se de que o repo foi clonado corretamente."
  exit 1
fi

# Garantir permissão de execução em todos os hooks versionados
chmod +x "$GITHOOKS_DIR"/* 2>/dev/null || true

# Apontar git para .githooks/ (persiste em .git/config local)
git -C "$REPO_ROOT" config core.hooksPath .githooks

echo "[DONE] core.hooksPath configurado para .githooks/"
echo "       Hooks ativos:"
for hook in "$GITHOOKS_DIR"/*; do
  echo "       - $(basename "$hook")"
done
