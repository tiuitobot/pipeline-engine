# Universal LLM Playbook for Pipelineable Work

## Metadata
- playbook_scope: universal
- version: 1.2.0
- last_updated: 2026-03-02
- owners: project-maintainers

## 1) Objective
Define a reusable operating model for LLM-driven implementation in repos with deterministic pipelines, contractual outputs, and auditability requirements.

## 1.1) Canonical Paths Contract (mandatory)
Each repo must define `config/playbook_paths.yaml` with explicit, machine-checkable paths:
- `metadata_file`
- `steps_dir`
- `pipelines_dir`
- `catalog_file`
- `manifest_pointer_file`
- `manifests_dir`
- `ledger_file`
- `validate_structure_cmd`
- `validate_contracts_cmd`
- `validate_version_bump_cmd`
- `pipeline_strict_cmd`

Without this file, playbook compliance is not enforceable.

## 2) Work Modes
### 2.1 Exploration mode
Use when the request is still under-specified.

Required short artifacts:
- `problem.md`: scope, question, exclusions
- `assumptions.md`: hypotheses and temporary decisions
- `acceptance.md`: objective definition of done
- `plan.md`: steps, risks, failure modes
- `contract_draft.json`: draft output contract

No canonical pipeline changes in this mode.
Allowed edits in exploration mode: `docs/` and `scratch/` only.
Do not edit canonical production sources (`steps/models`, `pipelines`, `config`, `contracts`) in exploration mode.

### 2.2 Production mode
Activate only after maturity gate passes.

Maturity gate (all required):
1. Inputs/variables and data sources are explicit.
2. Steps/models are explicit.
3. Output schema minimum is explicit.
4. Deliverables (tables/figures/files/APIs) have IDs and semantics.
5. Deterministic validations are explicit.

Required evidence locations:
- Inputs/sources in `problem.md` and metadata file
- Output schema in `contract_draft.json` (exploration) or `contracts/*.json` (production)
- Validation commands in `acceptance.md`

## 3) Non-negotiable Rules
1. Always produce machine-readable audit outputs.
2. Keep explicit contracts for outputs and deliverables.
3. Enforce version governance (SemVer) when semantics change.
4. Keep deterministic validation gates.
5. Keep canonical vs derived artifacts explicitly separated.
6. Keep a per-run manifest with hashes and a durable history ledger.
7. Keep metadata (`key-info` equivalent) synchronized with important project changes.

## 3.1) Canonical vs derived policy
- Canonical (manual edits allowed): `steps/`, `pipelines/`, `config/`, `contracts/`, metadata file, `docs/`.
- Derived (no manual edits): output artifacts, generated reports, run manifests, history ledger.
- Derived artifacts are generated only. Manual edits must fail validation gates.

## 3.2) Manifest and ledger minimum contract
Manifest (per run) must include:
- `generated_at`, `git_head`, `run_id`
- `schema_version`, `catalog_version`, `template_version` (directly or nested in version map)
- `inputs_fingerprint` (hash and/or immutable input references)
- `artifacts[]` with at least: `path`, `sha256`, `contract_id`

Ledger (append-only JSONL) must include:
- `ts`, `run_id`, `git_head`, `summary`, `manifest_sha256`

## 4) Generic Deterministic Protocol
1. Parse request into changes in inputs, steps, outputs, and validations.
2. Update project metadata.
3. Update implementation (`steps/` or equivalent).
4. Update orchestration (`pipelines/` or equivalent).
5. Update deliverables contract/catalog.
6. Run deterministic validators.
7. Execute strict run and generate output artifacts.
8. Confirm manifests, pointers, and version bumps.

Minimum universal validators that must exist in each repo:
- `validate_structure`
- `validate_contracts`
- `validate_version_bump`
- strict pipeline execution command

## 5) Multi-Agent Production Pipeline for Complex Deliverables

### 5.1) Trigger
Activate this protocol when the deliverable meets **any** condition:
1. 3+ distinct analytical blocks (e.g., multiple models, datasets, or methodologies).
2. 2+ output audiences (e.g., executive summary + technical appendix).
3. Detected inconsistencies between narrative claims and numerical outputs.
4. Final document exceeds 10 pages with tables/figures.

When none of these conditions apply, a single-agent workflow with justification in the project plan is acceptable.

### 5.2) Architecture: Sequential Pipeline with Single Source of Truth

Agents execute **synchronously** (one at a time, output feeds next) to avoid rate limits and ensure each stage builds on validated prior output.

The orchestrator (Main session) acts as **dispatcher + judge**: spawns each agent, evaluates output against acceptance criteria, decides advance or rework.

```
Main (orchestrator)
  → Agent 1: Data Auditor
  → Agent 2: Insight Explorer
  → Agent 3: Executive Writer
  → Agent 4: Technical Writer
  → Agent 5: Consistency Reviewer
  → Agent 6: Assembler
```

### 5.3) Agent Roles and Contracts

#### Agent 1 — Data Auditor
- **Purpose:** Transform raw pipeline outputs into a validated, single source of truth.
- **Input:** All machine-readable outputs from the pipeline (JSON, CSV, logs).
- **Output:**
  - `factsheet.json` — every key number, significance level, confidence interval, test result. Machine-readable.
  - `factsheet.md` — human-readable version with interpretation notes.
  - `data_quality.md` — flags, warnings, gaps, assumptions applied during extraction.
- **Acceptance criteria:**
  - Every numerical claim in the final deliverable MUST trace to a factsheet entry.
  - If a number is not in the factsheet, it does not exist for downstream agents.
- **Recommended model:** Cost-efficient (Codex/Sonnet). Task is extraction, not generation.

#### Agent 2 — Insight Explorer
- **Purpose:** Find non-obvious patterns, cross-model connections, and implications that the mechanical pipeline does not surface.
- **Input:** `factsheet.json` + raw outputs + source data.
- **Output:**
  - `insights.md` — ranked findings, each with: claim, evidence (referencing factsheet keys), relevance to the deliverable's audience.
- **Acceptance criteria:**
  - Every insight must reference factsheet evidence. No invented numbers.
  - Insights must be ranked by relevance to the target audience.
  - Must flag tensions or contradictions between analytical blocks.
- **Recommended model:** High-capability (Opus). Task requires reasoning across domains.

#### Agent 3 — Executive Writer
- **Purpose:** Write the executive summary and define the narrative arc for the entire deliverable.
- **Input:** `factsheet.md` + `insights.md` + prior version of deliverable (if exists, for tone reference).
- **Output:**
  - `executive_draft.md` — complete executive summary, structured progressively:
    1. Core message (1 paragraph, ≤3 sentences).
    2. Key findings (ordered to build progressive understanding — each creates curiosity for the next).
    3. Implications for the reader/decision-maker.
    4. Epistemic limits (what the analysis does NOT show).
    5. Reading guide (map to technical sections).
  - `narrative_arc.md` — skeleton defining tone, progression, and key claims for the Technical Writer to follow.
- **Acceptance criteria:**
  - All numbers from factsheet only.
  - Progressive structure: a reader who stops after the summary still gets the core message; one who continues is guided through increasing depth.
  - No overclaims. Non-significant results explicitly noted as such.
- **Recommended model:** High-capability (Opus). Task requires editorial judgment and audience awareness.

#### Agent 4 — Technical Writer
- **Purpose:** Write all detailed sections and appendices, following the narrative arc defined by Agent 3.
- **Input:** `factsheet.md` + `insights.md` + `narrative_arc.md` + deliverable catalog/config + figures/tables.
- **Output:**
  - `technical_sections.md` — all sections, clearly delimited, following catalog structure.
- **Acceptance criteria:**
  - Conclusions must not contradict the executive summary.
  - Every table/figure reference must exist in the catalog/output.
  - Methodology sections must be precise without redundancy.
  - Technical depth increases progressively (matching the narrative arc).
- **Recommended model:** High-capability (Opus) for analytical sections; cost-efficient (Codex/Sonnet) for mechanical appendices.

#### Agent 5 — Consistency Reviewer
- **Purpose:** Cross-check the entire deliverable against the factsheet and between sections.
- **Input:** `factsheet.json` + `executive_draft.md` + `technical_sections.md` + `insights.md` + deliverable catalog.
- **Output:**
  - `review_report.md` — itemized findings, each with:
    - Severity: `CRITICAL` (factual error), `HIGH` (narrative inconsistency), `MEDIUM` (clarity/style).
    - Location (section + paragraph).
    - Problem description.
    - Proposed fix (ready-to-apply text).
    - Evidence (factsheet reference).
- **Acceptance criteria:**
  - Zero `CRITICAL` items remaining before advancing to assembly.
  - `HIGH` items addressed or explicitly deferred with justification.
- **Recommended model:** High-capability (Opus). Task requires judgment across the full deliverable.

#### Agent 6 — Assembler
- **Purpose:** Apply reviewer corrections, assemble the final deliverable, and run validation gates.
- **Input:** `executive_draft.md` + `technical_sections.md` + `review_report.md` (corrections) + figures/templates/CSS.
- **Output:**
  - Final deliverable in target formats (HTML, PDF, DOCX as applicable).
  - Run manifest + ledger entry.
- **Acceptance criteria:**
  - All reviewer corrections applied.
  - Validation gates pass (structure, manifest, artifact policy, drift).
  - Pointers and state updated.
- **Recommended model:** Cost-efficient (Codex/Sonnet). Task is mechanical assembly, not generation.

### 5.4) Version Brief

Each pipeline run requires a `version-brief.md` in the project directory that documents **why** this version exists. It is the SSOT for intent and context.

**Required sections:**
- **§A. Context:** Study scope, audience, tone, previous version reference
- **§B. Reviewer Feedback:** Itemized feedback from stakeholders with classification
- **§C. Design Decisions:** Key methodological choices with justification
- **§D. Structural Changes:** Sections added, modified, removed, renamed

**Agent mapping:** Not all agents read the full brief. The orchestrator curates which sections each agent receives:
- Mechanical agents (Data Auditor, Assembler): no brief sections
- Creative agents (Writers): relevant sections per their function
- Quality agents (Reviewer): full brief as completeness checklist

The version-brief stays on disk and survives context compaction — it is the orchestrator's external memory for intent.

### 5.5) Orchestration Rules

1. **Sequential execution only.** Agent N+1 starts only after Agent N output is accepted by the orchestrator.
2. **Rework loop.** If an agent's output fails acceptance criteria, the orchestrator provides feedback and re-runs the same agent (max 2 retries before escalating to human).
3. **Factsheet as SSOT.** No downstream agent may introduce numbers not present in the factsheet. If a new number is needed, the pipeline returns to Agent 1.
4. **Spawn matrix required.** Before starting the pipeline, the orchestrator must create `plans/<project>/spawn-matrix.md` with:
   - Objective per agent.
   - Expected artifact.
   - Acceptance criteria.
   - Conflict resolution rule (which agent's output prevails).
5. **Evidence trail.** All intermediate artifacts are preserved in the project's output directory for auditability.

### 5.6) Orchestrator Contract

The orchestrator session (Main/Opus) operates under a dedicated contract that prevents context bloat and enforces sequential discipline. See `docs/contracts/CONTRACT-00-orchestrator.md` for the full specification.

**Key constraints (summary):**
- R1: Never read data files into orchestrator context (agents read their own inputs)
- R2: Agent returns = status + path only (no file content in messages)
- R3: One agent at a time (sequential dispatch)
- R4: Agent failure → re-delegate, never absorb into orchestrator
- R5: Poll timeout 5 min, interval 30s, max 10 polls per agent
- R6: All outputs to accumulation path (agents read from disk, not from orchestrator)
- R7: spawn-matrix.md required before first spawn

**Enforcement:** `scripts/validate_orchestrator_contract.sh` (pre-pipeline gate)

### 5.7) Adaptation per Project

The repo-specific playbook (`docs/llm_playbook.md`) may customize:
- Which agents are needed (some projects may skip Agent 2 if no cross-model analysis applies).
- Specific checklist items per agent (domain vocabulary, audience, format requirements).
- Model assignments per agent.
- Additional gates or acceptance criteria.

The repo-specific adaptation **must not remove** the factsheet-as-SSOT rule or the consistency review stage. These are structural invariants.

### 5.7) Relation to ADR-026
This section generalizes the protocol originally defined in ADR-026 (Compartmented Multi-Spawn for Complex Technical Work). ADR-026 remains the decision record; this section is the operational specification.

## 6) Version Policy (Generic)
*[Was Section 5 in v1.0.x]*
- `schema_version`: structure of contracts.
- `catalog_version`: semantic content of deliverables.
- `template_version`: rendering/packaging baseline.

Bump rules:
- MAJOR: breaking semantic/structure change.
- MINOR: additive compatible change.
- PATCH: non-breaking correction.

## 7) Idempotency Policy
Same input and config should produce:
- same schema and validation outcomes always;
- same hashes when deterministic;
- documented, bounded differences when stochastic.

Stochastic differences must be documented in metadata and/or assumptions files.

## 8) Definition of Done
1. Requested change implemented.
2. Contracts and deliverables updated.
3. Validation gates pass.
4. Strict run succeeds.
5. Metadata updated.
6. Manifest + ledger updated.
7. Rollback path to previous active version is explicit.

## 9) Stakeholder Feedback Review Protocol

When receiving feedback on a deliverable (docx with comments, email, verbal notes, annotated PDF), the review must be **exhaustive**. Partial extraction = missed requirements = rework.

### 9.1) Extraction Checklist (mandatory, sequential)
For any feedback document, extract **all** of the following layers:

| Layer | What to extract | How |
|-------|----------------|-----|
| 1. Explicit comments | Margin comments, annotations, review notes | Parse `comments.xml` (docx), annotation objects (PDF), or transcribe verbatim |
| 2. Track changes — deletions | Text the reviewer removed | Parse `<w:del>` elements (docx) or strikethrough markup |
| 3. Track changes — insertions | Text the reviewer added | Parse `<w:ins>` elements (docx) or highlighted additions |
| 4. Format changes | Heading level changes, renumbering, style modifications | Parse `<w:rPrChange>`, `<w:pPrChange>` (docx) |
| 5. Structural signals | Renumbering of sections, reordering, new subsection hints | Infer from insertion/deletion patterns and numbering changes |
| 6. Implicit intent | What the reviewer *wants* but didn't spell out | Infer from the combination of changes — document as hypothesis, not fact |

### 9.2) Cross-referencing Rule
Each extracted item must be cross-referenced against:
1. **Current deliverable** — what does the current version say in that location?
2. **Project playbook** — is the request consistent with established contracts and audience?
3. **Data/model outputs** — can the request be satisfied with existing data, or does it require re-execution?

### 9.3) Classification of Changes
Every feedback item must be classified:

| Type | Definition | Requires |
|------|-----------|----------|
| **Report-only** | Text/structure change, no model impact | Regenerate report, validate catalog |
| **Data-dependent** | Needs values from model outputs not currently in report | Extract from outputs, then report-only |
| **Model-impacting** | Requires re-estimation or new analysis | Full pipeline re-run |
| **Ambiguous** | Reviewer intent is unclear | Clarify with stakeholder before implementing |

### 9.4) Output Format
The review must produce a **structured feedback digest** before any implementation begins:

```
## Feedback Digest — [deliverable] [reviewer] [date]

### Comments (N items)
| # | Location | Reviewer request | Classification | Action |

### Track Changes (N items)
| # | Type (ins/del/fmt) | Content | Interpretation | Action |

### Inferred Structural Changes
- [description and evidence]

### Questions for Reviewer (if any)
- [ambiguous items requiring clarification]

### Implementation Plan
| Priority | Action | Section | Type | Blocked by |
```

### 9.5) Completeness Gate (self-check)
Before declaring the review complete, verify:
- [ ] `comments.xml` (or equivalent) fully parsed — count matches expected
- [ ] Track changes (insertions + deletions) fully parsed — count matches expected
- [ ] Format/structural changes identified
- [ ] Every item classified (report-only / data-dependent / model-impacting / ambiguous)
- [ ] Cross-referenced against playbook and current deliverable
- [ ] No layer from §9.1 was skipped

> **Anti-pattern:** Extracting only comments and missing track changes. This happened and caused incomplete analysis. The protocol exists to prevent recurrence.
