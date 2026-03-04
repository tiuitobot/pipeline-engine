# assumptions.md — pipeline-engine

## Design Assumptions

### Orchestration
- Sequential execution is the default: Agent N must complete before Agent N+1 starts
- Parallel spawns are allowed only for independent scouts (web research, data ingestion) that have no dependency on other agents
- `pipeline-state.json` is the SSOT for pipeline execution state — it survives orchestrator context compaction
- The spawn-once-send-sync pattern (spawn worker with mode="run", reuse via sessions_send) is the standard primitive

### Validation
- R10a validation is extensible via plugins — each project implements its own plugin or uses PassthroughPlugin
- Validation is mechanical (deterministic scripts), not LLM-based
- An agent output that fails R10a triggers rework (max 2 retries), not pipeline abort

### Models
- Any LLM model can be an agent (Opus, Sonnet, Codex, GPT)
- Orchestrator should be lightweight (Codex or Sonnet) — data collection + dispatch, not synthesis
- Consumer/synthesis agents should be high-capability (Opus) — judgment, routing, quality
- Model assignment is defined per-agent in spawn-matrix, not hardcoded in the engine

### Generality
- The engine is domain-agnostic — it does not embed any econometric, fiscal, or domain-specific logic
- Domain logic lives entirely in the consumer repo (steps/, models/, pipelines/)
- Templates use {PLACEHOLDER} tokens — consumer must fill before activating

### Governance
- playbook-universal.md is the normative spec — this repo implements §5 mechanically
- §1-§4 and §6-§9 are governance that consumer repos must follow
- This repo itself follows the playbook (eats its own dogfood): config/playbook_paths.yaml present, problem/assumptions/acceptance defined
