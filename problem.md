# problem.md — pipeline-engine

## Scope
Generic, reusable engine for orchestrating multi-agent LLM pipelines.
Extracted from `var-cambio-icms` after 14 production pipeline iterations (v14 scored 9.00/10 in independent Opus audit).

## Question
How do we enable any new project to use a production-grade multi-agent pipeline without re-implementing the orchestration layer from scratch?

Every new project that needs LLM agents currently must:
- Re-invent state management (which agent is next, what failed, what passed)
- Re-invent R10a validation (mechanical checks on agent outputs)
- Re-invent spawn-matrix parsing and dispatch logic
- Re-write contracts, templates, and runbooks from zero

This repo solves that by extracting the invariant orchestration layer.

## Exclusions
- Domain-specific logic (belongs in the consumer repo — models, data pipelines, report formatting)
- Agent task definitions (defined per-project in `spawn-matrix.md`)
- Data ingestion and transformation (consumer repo responsibility)
- Any LLM-specific API calls (engine dispatches agents, does not call LLMs directly)

## Origin
Extracted from `var-cambio-icms` (tiuitobot/var-cambio-icms) — econometric pipeline with 8-agent architecture, R10a mechanical validation, and spawn-once-send-sync orchestration pattern.
