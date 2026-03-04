#!/usr/bin/env bash
set -euo pipefail

# Usage: new_pipeline.sh <target-dir> [--name <project-name>]
# Bootstrap a new multi-agent pipeline project using pipeline-engine as base.

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <diretório-destino> [--name <nome-do-projeto>]"
  echo "Exemplo: $0 ~/repos/meu-pipeline --name meu-pipeline"
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$1"
PROJECT_NAME="${TARGET##*/}"  # default: basename do diretório

shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) PROJECT_NAME="$2"; shift 2 ;;
    *) echo "[WARN] Argumento desconhecido: $1"; shift ;;
  esac
done

NOW_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TODAY="$(date -u +%Y-%m-%d)"

echo "[1/7] Criando estrutura de diretórios..."
mkdir -p "$TARGET"/{config,docs/contracts,templates,scripts/r10_plugins,outputs/active,scratch,plans}

echo "[2/7] Copiando engine, plugins e hooks..."
cp "$ROOT/scripts/pipeline_engine.py" "$TARGET/scripts/pipeline_engine.py"
cp -R "$ROOT/scripts/r10_plugins/." "$TARGET/scripts/r10_plugins/"
cp "$ROOT/scripts/validate_r10a.py" "$TARGET/scripts/validate_r10a.py"
cp "$ROOT/scripts/validate_playbook_checksums.py" "$TARGET/scripts/validate_playbook_checksums.py"
cp "$ROOT/scripts/install_git_hooks.sh" "$TARGET/scripts/install_git_hooks.sh"

# Copiar hooks versionados (P139: gate não-versionado = gate que desaparece)
if [[ -d "$ROOT/.githooks" ]]; then
  mkdir -p "$TARGET/.githooks"
  cp -R "$ROOT/.githooks/." "$TARGET/.githooks/"
  chmod +x "$TARGET/.githooks"/* 2>/dev/null || true
fi

echo "[3/7] Copiando playbook e templates..."
cp "$ROOT/docs/playbook-universal.md" "$TARGET/docs/playbook-universal.md"
cp -R "$ROOT/templates/." "$TARGET/templates/"

echo "[4/7] Gerando config/playbook_paths.yaml..."
PLAYBOOK_SHA=$(sha256sum "$TARGET/docs/playbook-universal.md" | awk '{print $1}')
cat > "$TARGET/config/playbook_paths.yaml" <<EOF
{
  "schema_version": 1,
  "contract_version": "1.0.0",
  "playbook_checksums": {
    "docs/playbook-universal.md": "$PLAYBOOK_SHA"
  },
  "metadata_file": "key-info.json",
  "templates_dir": "templates",
  "scripts_dir": "scripts",
  "docs_dir": "docs",
  "validate_structure_cmd": "python3 scripts/validate_playbook_checksums.py",
  "canonical_paths": [
    "docs/",
    "scripts/",
    "templates/",
    "config/",
    "plans/",
    "key-info.json"
  ],
  "derived_paths": [
    "outputs/"
  ]
}
EOF

echo "[5/7] Gerando key-info.json..."
cat > "$TARGET/key-info.json" <<EOF
{
  "repo": "$PROJECT_NAME",
  "version": 1,
  "lastUpdated": "$NOW_ISO",
  "keyInfo": [
    {
      "id": "K001",
      "info": "project_name: $PROJECT_NAME",
      "importance": "high",
      "status": "confirmed",
      "date": "$TODAY",
      "source": "bootstrap via pipeline-engine/new_pipeline.sh"
    },
    {
      "id": "K002",
      "info": "description: (preencher)",
      "importance": "high",
      "status": "draft",
      "date": "$TODAY",
      "source": "bootstrap"
    },
    {
      "id": "K003",
      "info": "pipeline_engine_source: $ROOT",
      "importance": "medium",
      "status": "confirmed",
      "date": "$TODAY",
      "source": "bootstrap"
    }
  ]
}
EOF

echo "[6/7] Gerando docs de exploração..."
cat > "$TARGET/problem.md" <<EOF
# problem.md — $PROJECT_NAME

## Scope
(Descreva o escopo do projeto — o que está incluído e o domínio.)

## Question
(Qual a pergunta central que este pipeline responde?)

## Exclusions
(O que explicitamente NÃO faz parte deste projeto.)

## Origin
Bootstrapped from pipeline-engine on $TODAY.
EOF

cat > "$TARGET/assumptions.md" <<EOF
# assumptions.md — $PROJECT_NAME

## Design Assumptions

### Pipeline
- Número de agentes: (definir na spawn-matrix)
- Modelo do orquestrador: (codex/sonnet — lightweight)
- Modelo dos agentes de síntese: (opus — high capability)

### Domain
- (Listar premissas específicas do domínio)

### Validation
- Plugin R10a: (passthrough / numeric_factsheet / custom)
EOF

cat > "$TARGET/acceptance.md" <<EOF
# acceptance.md — $PROJECT_NAME

## Definition of Done

### Structural
- [ ] config/playbook_paths.yaml exists and checksum matches
- [ ] problem.md preenchido com escopo real
- [ ] spawn-matrix.md definida em plans/
- [ ] version-brief.md definida em plans/

### Pipeline
- [ ] Pipeline executa do Agent 0 ao último sem falhas
- [ ] R10a validation passa para todos os agentes com plugin configurado
- [ ] Output final gerado em outputs/active/

### Quality
- [ ] (Definir critérios de qualidade específicos do domínio)
EOF

echo "[7/7] Gerando .gitignore..."
cat > "$TARGET/.gitignore" <<'EOF'
scratch/
*.pyc
__pycache__/
venv/
outputs/active/*.pdf
.env
EOF

echo ""
echo "✅ Bootstrap criado em: $TARGET"
echo ""
echo "Próximos passos:"
echo "  1. cd $TARGET && git init"
echo "  2. bash scripts/install_git_hooks.sh   ← ativa pre-commit gate (repo_doctor)"
echo "  3. Preencher problem.md com escopo real"
echo "  4. Criar plans/spawn-matrix.md (copiar de templates/)"
echo "  5. Criar plans/version-brief.md (copiar de templates/)"
echo "  6. python3 scripts/validate_playbook_checksums.py  (deve PASS)"
echo "  7. Rodar pipeline: python3 scripts/pipeline_engine.py --init ..."
