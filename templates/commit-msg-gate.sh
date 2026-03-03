#!/usr/bin/env bash
# Nível 2 — Playbook Protocol Reference Gate
# Requires commit messages to reference a playbook step or be explicitly exempt.
#
# Valid patterns:
#   §4.1: parse request ...
#   §4.3: update implementation ...
#   §3: non-negotiable rule ...
#   §9: pipeline agent ...
#   playbook-exempt: reason
#   merge commit (auto-generated)
#   Revert "..."
#
# Skip: SKIP_PLAYBOOK_GATE=1 git commit ...
set -euo pipefail

if [[ "${SKIP_PLAYBOOK_GATE:-0}" == "1" ]]; then
  exit 0
fi

MSG_FILE="$1"
MSG="$(head -1 "$MSG_FILE")"

# Allow merge commits
if [[ "$MSG" =~ ^Merge ]]; then
  exit 0
fi

# Allow reverts
if [[ "$MSG" =~ ^Revert ]]; then
  exit 0
fi

# Check for playbook reference (§N or §N.N) or explicit exemption
if echo "$MSG" | grep -qE '§[0-9]+|playbook-exempt:'; then
  exit 0
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  PLAYBOOK PROTOCOL GATE (Nível 2)                          ║"
echo "║                                                             ║"
echo "║  Commit message must reference a playbook section:          ║"
echo "║    §4.1: parse request into changes                         ║"
echo "║    §4.2: update project metadata                            ║"
echo "║    §4.3: update implementation                              ║"
echo "║    §4.4: update orchestration                               ║"
echo "║    §4.5: update deliverables contract/catalog               ║"
echo "║    §4.6: run deterministic validators                       ║"
echo "║    §4.7: execute strict run                                 ║"
echo "║    §4.8: confirm manifests/pointers/version bumps           ║"
echo "║    §3: non-negotiable rule enforcement                      ║"
echo "║    §5/§9: pipeline multi-agent                              ║"
echo "║                                                             ║"
echo "║  Or use: playbook-exempt: <reason>                          ║"
echo "║  Or set: SKIP_PLAYBOOK_GATE=1                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Your message: $MSG"
echo ""
exit 1
