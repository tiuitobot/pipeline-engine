#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

failures=()

check_file_exists() {
  local path="$1"
  local label="$2"

  if [[ -e "$path" ]]; then
    echo "[PASS] $label"
  else
    echo "[FAIL] $label"
    failures+=("$label")
  fi
}

check_file_exists "config/playbook_paths.yaml" "config/playbook_paths.yaml exists"
check_file_exists "problem.md" "problem.md exists"
check_file_exists "assumptions.md" "assumptions.md exists"
check_file_exists "acceptance.md" "acceptance.md exists"
check_file_exists "docs/playbook-universal.md" "docs/playbook-universal.md exists"
check_file_exists "scripts/pipeline_engine.py" "scripts/pipeline_engine.py exists"

if [[ ! -d "templates" ]]; then
  echo "[FAIL] templates placeholder token check"
  failures+=("templates placeholder token check")
else
  template_fail=0
  while IFS= read -r -d '' file; do
    if ! grep -qE '\{[A-Za-z0-9_:-]+\}' "$file"; then
      echo "[FAIL] $(realpath --relative-to="$ROOT" "$file") missing placeholder token {…}"
      failures+=("$(realpath --relative-to="$ROOT" "$file") missing placeholder token {…}")
      template_fail=1
    fi
  done < <(find templates -maxdepth 1 -type f -print0 | sort -z)

  if [[ "$template_fail" -eq 0 ]]; then
    echo "[PASS] templates placeholder token check"
  fi
fi

if python3 scripts/validate_playbook_checksums.py >/tmp/repo_doctor_checksum.log 2>&1; then
  echo "[PASS] validate_playbook_checksums.py"
else
  echo "[FAIL] validate_playbook_checksums.py"
  failures+=("validate_playbook_checksums.py")
  sed 's/^/  /' /tmp/repo_doctor_checksum.log
fi

if [[ ${#failures[@]} -gt 0 ]]; then
  echo ""
  echo "[REPO DOCTOR] Failed checks:"
  for failure in "${failures[@]}"; do
    echo "- $failure"
  done
  exit 1
fi

echo "[REPO DOCTOR] All checks passed."
