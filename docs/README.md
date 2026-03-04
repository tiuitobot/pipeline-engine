# Documentation Index

## Specification
- [`playbook-universal.md`](playbook-universal.md) — Universal LLM Pipeline Playbook
  - §1-§2: Work modes (exploration → production) + maturity gate
  - §3: Non-negotiable rules (audit outputs, contracts, SemVer, validation gates)
  - §4: Generic deterministic protocol (8-step)
  - §5: **Multi-agent pipeline** — 8-agent architecture (Agent 0–7), orchestration rules (R1–R15), version brief, contracts
  - §6-§7: Version policy + idempotency
  - §8: Definition of Done
  - §9: Stakeholder feedback protocol

## Agent Architecture (§5)
| Agent | Role | Model | Purpose |
|-------|------|-------|---------|
| 0 | Domain Specialist | opus | Entry gate — context evaluation, proceed/pause_for_code |
| 1 | Data Auditor | codex | Factsheet extraction (SSOT for numbers) |
| 2 | Insight Explorer | opus | Cross-model analysis, tensions, implications |
| 3 | Executive Writer | opus | Narrative arc, executive summary |
| 4 | Technical Writer | opus | Detailed sections, appendices |
| 5 | Consistency Reviewer | opus | Cross-check factsheet ↔ narrative |
| 6 | Assembler | codex | Final assembly, validation gates |
| 7 | External Auditor | gpt | Cold audit — independent provider, score 1-10 |

## Quick Links
- [Main README](../README.md) — usage guide, templates, examples
- [Templates](../templates/) — CONTRACT-00, spawn-matrix, version-brief, runbook
- [Examples](../examples/) — econometric-report (8 agents), teaching-materials (7 agents)
