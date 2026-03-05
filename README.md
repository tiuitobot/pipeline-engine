# pipeline-engine

Framework genérico e domain-agnostic para execução de **pipelines multi-agente sequenciais** com LLMs, extraído de produção real.

> **Especificação completa:** [`docs/playbook-universal.md`](docs/playbook-universal.md) — este é o documento de governança que o engine implementa.

## O que é

Um engine que orquestra N agentes LLM em sequência, onde cada agente:
1. Recebe inputs definidos em uma **spawn-matrix** (markdown table)
2. Produz um artefato no path especificado
3. É validado mecanicamente por um **plugin R10a** (factsheet↔texto, schema, etc.)
4. Tem seu estado registrado em **pipeline-state.json** (SSOT)

O engine é **agnóstico de domínio** — funciona para relatórios econométricos, material didático, documentação técnica ou qualquer entregável estruturado.

## Navegação rápida

| Arquivo | Função |
|---------|--------|
| [`docs/playbook-universal.md`](docs/playbook-universal.md) | Especificação completa — governança, regras, protocolo determinístico, pipeline §5 |
| [`scripts/pipeline_engine.py`](scripts/pipeline_engine.py) | Engine CLI — init, dispatch, record, status |
| [`scripts/new_pipeline.sh`](scripts/new_pipeline.sh) | Bootstrap one-shot de um novo projeto pipeline com estrutura mínima |
| [`scripts/repo_doctor.sh`](scripts/repo_doctor.sh) | Validador estrutural do repositório (artefatos mandatórios + checksums) |
| [`scripts/r10_plugins/`](scripts/r10_plugins/) | Plugins de validação mecânica (R10a) |
| [`templates/`](templates/) | Contratos, runbook, spawn-matrix, version-brief (prontos para copiar) |
| [`examples/`](examples/) | Configurações de exemplo: relatório econométrico + material didático |

## Como usar para um projeto novo

### 1. Bootstrap one-shot (recomendado)
```bash
bash scripts/new_pipeline.sh <target-dir>
```

Esse comando cria a estrutura mínima do projeto, copia engine/plugins/templates e gera arquivos iniciais obrigatórios.

> **Nota importante:** `pipeline_engine.py --init` recusa inicializar se `repo_doctor.sh` falhar.

### 2. Inicializar e rodar
```bash
# Inicializar state
python3 scripts/pipeline_engine.py \
  --accumulation-dir outputs/active/metadata/v1 \
  --init

# Dispatch (mostra próximo agente a executar)
python3 scripts/pipeline_engine.py \
  --accumulation-dir outputs/active/metadata/v1 \
  --dispatch

# Registrar conclusão de agente
python3 scripts/pipeline_engine.py \
  --accumulation-dir outputs/active/metadata/v1 \
  --record-completion --agent-number 0 \
  --result done --output-path outputs/active/metadata/v1/agent0.md

# Registrar R10a (validação mecânica)
python3 scripts/pipeline_engine.py \
  --accumulation-dir outputs/active/metadata/v1 \
  --record-r10a --agent-number 0 \
  --r10a-path outputs/active/metadata/v1/r10_mechanical_agent_0.json
```

### Alternativa: setup manual

Se preferir montar tudo manualmente, siga este fluxo:

#### A. Copiar templates para o seu repo
```bash
# No seu repo de destino:
cp -r /path/to/pipeline-engine/templates/ docs/contracts/
cp /path/to/pipeline-engine/scripts/pipeline_engine.py scripts/
cp -r /path/to/pipeline-engine/scripts/r10_plugins/ scripts/r10_plugins/
```

#### B. Criar spawn-matrix do seu projeto
Use `templates/spawn-matrix-template.md` como base. Defina:
- Número e nome de cada agente
- Modelo LLM por agente (opus, codex, sonnet, gpt)
- Timeout por agente
- Paths de input e output
- Task description e acceptance criteria

#### C. Criar version-brief
Use `templates/version-brief-template.md`. Descreva:
- O que muda nesta versão vs anterior
- Diretrizes editoriais (audiência, tom, foco)
- Inputs disponíveis

#### D. Configurar contrato do orquestrador
Preencha `templates/CONTRACT-00-template.md` com as regras do seu pipeline:
- Budget de contexto do orquestrador
- Protocolo de falha e rework
- Regras R10-R16 (quais aplicam)

## Padrão de orquestração: spawn-once-send-sync

O engine foi desenhado para funcionar com o padrão **spawn-once-send-sync** do OpenClaw:

1. **Spawn** um worker com `mode="run"` (sessão persiste após conclusão)
2. **Reutilize** via `sessions_send(timeoutSeconds=N)` — chamada síncrona, bloqueia até resposta
3. **State file** (`pipeline-state.json`) é o SSOT — sobrevive a compactação do orquestrador
4. **Watchdog** (opcional) monitora estado e nudges o orquestrador se necessário

Este padrão resolve o problema de auto-announce assíncrono e elimina a necessidade de polling.

## Plugins R10a

O sistema de validação mecânica é extensível via plugins:

| Plugin | Uso |
|--------|-----|
| `PassthroughPlugin` | Sempre PASS — para agentes sem validação mecânica aplicável |
| `NumericFactsheetPlugin` | Valida consistência numérica entre factsheet JSON e texto |

### Criar plugin customizado
```python
from r10_plugins.base_plugin import BaseR10Plugin

class MeuPlugin(BaseR10Plugin):
    def validate(self, agent_output_path, reference_data_path, agent_number):
        # ... lógica de validação ...
        return {"status": "pass", "checks": [...], "errors": [...]}
```

## Templates incluídos

| Template | Propósito |
|----------|-----------|
| `CONTRACT-00-template.md` | Contrato do orquestrador (R1-R16) |
| `CONTRACT-00-addendum-sync-template.md` | Addendum spawn-once-send-sync |
| `ORCHESTRATOR-RUNBOOK-template.md` | Runbook operacional do orquestrador |
| `spawn-matrix-template.md` | Spawn matrix com placeholders |
| `version-brief-template.md` | Version brief template |

Todos contêm `{PLACEHOLDER}` tokens para substituir com valores do seu projeto.

## Exemplos

### Relatório econométrico (`examples/econometric-report/`)
Pipeline de 8 agentes para relatório de análise econométrica:
Domain Specialist → Data Auditor → Insight Explorer → Executive Writer → Technical Writer → Consistency Reviewer → Assembler → External Auditor

### Material didático (`examples/teaching-materials/`)
Pipeline de 6 agentes para pacote de aula:
Curriculum Analyzer → Lesson Planner → Slide Writer → Exercise Creator → Pedagogical Reviewer → Materials Assembler

## Relação com o playbook universal

O [`docs/playbook-universal.md`](docs/playbook-universal.md) é a **especificação completa** que este engine implementa:

- **§1-§2**: Modos de trabalho (exploração vs produção) e maturity gate
- **§3**: Regras não-negociáveis (audit outputs, contracts, SemVer, validation gates)
- **§4**: Protocolo determinístico de 8 passos
- **§5**: Pipeline multi-agente — arquitetura, papéis, regras de orquestração
- **§6-§7**: Versão e idempotência
- **§8**: Definition of Done
- **§9**: Protocolo de feedback de stakeholders

O engine implementa §5 mecanicamente. As demais seções são governança que o repo consumidor deve seguir.

## Origem

Extraído do repo [var-cambio-icms](https://github.com/tiuitobot/var-cambio-icms) após 14 versões de relatório executivo com pipeline multi-agente. O engine v14 alcançou score 9.00/10 em auditoria independente (Opus).
