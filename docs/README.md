# Pipeline Engine

Generic, domain-agnostic engine to run sequential multi-agent pipelines using:
- `spawn-matrix.md` (execution plan)
- `pipeline-state.json` (runtime state)
- R10a plugin validations (mechanical checks)

This repo was extracted and generalized from a production multi-agent pipeline implementation.

## What it includes
- `scripts/pipeline_engine.py` — engine CLI + `PipelineEngine` class
- `scripts/r10_plugins/` — plugin system for mechanical validations
- `templates/` — reusable contracts, runbook, and planning templates
- `examples/` — sample configs for two domains
- `docs/playbook-universal.md` — universal LLM pipeline playbook

## Quick start

```bash
cd /home/linuxadmin/repos/pipeline-engine

# 1) Prepare run directory (example)
mkdir -p outputs/active/metadata/v1
cp templates/spawn-matrix-template.md outputs/active/metadata/v1/spawn-matrix.md

# 2) Initialize state
python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v1 --init

# 3) Attach worker session key (from your orchestration layer)
python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v1 --set-worker <SESSION_KEY>

# 4) Dispatch next task
python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v1 --dispatch

# 5) Record completion + R10a
python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v1 --record-completion --agent-number 0 --result done --output-path outputs/active/metadata/v1/agent0.md
python3 scripts/pipeline_engine.py --accumulation-dir outputs/active/metadata/v1 --record-r10a --agent-number 0 --r10a-path outputs/active/metadata/v1/r10_mechanical_agent_0.json
```

## Python import

```python
from pipeline_engine import PipelineEngine
```

## R10a plugin interface

Plugins must implement:

```python
def validate(agent_output_path: str, reference_data_path: str, agent_number: int) -> dict
```

Available plugins:
- `r10_plugins.passthrough.PassthroughPlugin`
- `r10_plugins.numeric_factsheet.NumericFactsheetPlugin`
