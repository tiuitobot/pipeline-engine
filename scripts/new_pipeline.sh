#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Uso: $0 <diretório-destino>"
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$1"

mkdir -p "$TARGET/docs/contracts"
mkdir -p "$TARGET/templates"
mkdir -p "$TARGET/scripts"
mkdir -p "$TARGET/outputs/active"
mkdir -p "$TARGET/scratch"
mkdir -p "$TARGET/plans"

cp "$ROOT/docs/playbook-universal.md" "$TARGET/docs/playbook-universal.md"
cp -R "$ROOT/templates/." "$TARGET/templates/"
cp "$ROOT/scripts/pipeline_engine.py" "$TARGET/scripts/pipeline_engine.py"
cp -R "$ROOT/scripts/r10_plugins" "$TARGET/scripts/r10_plugins"
cp "$ROOT/scripts/validate_r10a.py" "$TARGET/scripts/validate_r10a.py"

if [[ -f "$ROOT/templates/key-info-template.json" ]]; then
  cp "$ROOT/templates/key-info-template.json" "$TARGET/key-info.json"
  sed -i \
    -e 's/{PROJECT_NAME}/{PLACEHOLDER}/g' \
    -e 's/{PROJECT_DESCRIPTION}/{PLACEHOLDER}/g' \
    -e 's/{PIPELINE_VERSION}/{PLACEHOLDER}/g' \
    -e 's/{SPAWN_MATRIX_FILE}/{PLACEHOLDER}/g' \
    "$TARGET/key-info.json"
else
  cat > "$TARGET/key-info.json" <<'EOF'
{
  "repo": "{PLACEHOLDER}",
  "version": 1,
  "lastUpdated": "{YYYY-MM-DDTHH:MM:SS-03:00}",
  "keyInfo": [
    {
      "id": "K001",
      "info": "project_name: {PLACEHOLDER}",
      "importance": "high",
      "status": "confirmed",
      "date": "{YYYY-MM-DD}",
      "source": "bootstrap"
    }
  ]
}
EOF
fi

cat > "$TARGET/problem.md" <<'EOF'
## Scope

## Question

## Exclusions

## Origin
EOF

cat > "$TARGET/assumptions.md" <<'EOF'
## Design Assumptions
EOF

cat > "$TARGET/acceptance.md" <<'EOF'
## Definition of Done

## Acceptance Criteria
EOF

cat > "$TARGET/.gitignore" <<'EOF'
scratch/
*.pyc
__pycache__/
venv/
outputs/active/*.pdf
EOF

echo "Bootstrap criado em: $TARGET — próximo passo: preencher problem.md e definir spawn-matrix"
