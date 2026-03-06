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

### 5.0) Solo-First Protocol (mandatory pre-condition)

**Rule: The main agent must produce a solid v1 before activating multi-agent orchestration.**

The deterministic scaffold (repo structure, `pipeline-state.json`, metadata tracking, auditing) should be used from day one. But agentic orchestration (multi-agent dispatch with formal contracts) must NOT be activated until:

1. **A working v1 exists**, produced by the main agent (Opus) directly.
2. **At least one feedback cycle** with the human has occurred (corrections applied, direction confirmed).
3. **The document/deliverable has grown beyond what one agent can hold in context** (typically >30 pages or 3+ independent data sources).

**Rationale (evidence-based):**
- var-cambio-icms: versions 1–10 were produced by Opus solo. Pipeline entered at v11 (~60 pages, multiple sources). Result: 7/10 client score on first pipeline run.
- Lucas: pipeline activated at v1 (single source, single domain). Result: 6/10 client score on v1, data inconsistencies on v2 (889-question gap missed by all agents).
- Root cause: pipeline scales existing quality — it does not create initial quality. Delegating v1 to subagents removes the main agent's contextual judgment during the critical formation phase.

**Solo phase workflow:**
```
Main (Opus) does everything:
  → Parse source material
  → Collect/scrape external data
  → Write content
  → Generate visuals (or delegate 1 mechanical codex worker)
  → Self-review with consistency checks
  → Deliver v1 → human feedback → iterate
```

**Graduation criteria (all required to activate §5.1):**
- [ ] v1 delivered and reviewed by human
- [ ] Document exceeds single-context threshold (>30 pages OR 3+ independent sources)
- [ ] Iterative corrections stabilized (no fundamental structural changes in last 2 versions)

### 5.1) Trigger
Activate this protocol when **§5.0 graduation criteria are met** AND the deliverable meets **any** condition:
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
  → Agent 0: Domain Specialist        [opus]    — context + proceed/pause gate
  → Agent 1: Data Auditor             [codex]   — factsheet extraction
  → Agent 2: Insight Explorer         [opus]    — cross-model analysis
  → Agent 3: Executive Writer         [opus]    — narrative + executive summary
  → Agent 4: Technical Writer         [opus]    — detailed sections
  → Agent 5: Consistency Reviewer     [opus]    — cross-check
  → Agent 6: Assembler                [codex]   — final assembly
  → Agent 7: External Auditor         [gpt]     — cold audit (independent provider)
```

**Agent 0** is the entry gate: it evaluates whether the project context is sufficient to proceed or requires human input (code, data, configuration). If Agent 0 recommends `pause_for_code`, the pipeline halts and reports what is needed.

**Agent 7** runs as the exit gate: it receives ONLY the final assembled deliverable and key-info.json — no intermediate artifacts. This ensures an independent quality assessment. Using a different model provider (e.g., GPT when the pipeline uses Claude) further increases independence.

### 5.3) Agent Roles and Contracts

#### Agent 0 — Domain Specialist
- **Purpose:** Evaluate project context, domain constraints, and data readiness before the pipeline begins data processing. Acts as the entry gate.
- **Input:** `version-brief.md` + `key-info.json` + domain reference materials (if available).
- **Output:**
  - `domain_analysis.md` or `research_proposals.md` — context evaluation with one of two recommendations:
    - `proceed` — context is sufficient, pipeline can continue to Agent 1.
    - `pause_for_code` — human input required (missing data, code, configuration). Lists exactly what is needed.
- **Acceptance criteria:**
  - Recommendation is explicit (`proceed` or `pause_for_code`) with justification.
  - If `proceed`: identifies key domain constraints that downstream agents must respect.
  - If `pause_for_code`: lists concrete items needed (not vague requests).
- **Recommended model:** High-capability (Opus). Task requires domain judgment and strategic evaluation.

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

#### Agent 7 — External Auditor
- **Purpose:** Independent cold audit of the final deliverable. Has NO access to intermediate artifacts — evaluates only what a reader would see.
- **Input:** Final assembled deliverable (HTML/PDF from Agent 6) + `key-info.json` only.
- **Output:**
  - `external_audit.md` — structured audit report with:
    - Numeric score (1-10) with criteria breakdown (accuracy, completeness, consistency, clarity).
    - Issues listed by severity: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
    - Specific recommendations per issue (actionable, not vague).
    - Overall assessment: pass (≥7), conditional pass (5-6), fail (<5).
- **Acceptance criteria:**
  - Score is justified with evidence from the deliverable.
  - Each issue has: location, description, severity, proposed fix.
  - Auditor must NOT have access to factsheet, insights, or review reports (cold audit invariant).
- **Recommended model:** Different provider preferred (GPT when pipeline uses Claude, or vice versa). Independence > capability for this role.
- **Note:** This agent was introduced after v11 (var-cambio-icms) when internal review alone proved insufficient to catch structural inconsistencies. The external audit added 15 min to the pipeline but caught issues that increased the final score from 7/10 to 9/10.

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
6. **Agent 0 gate.** If Agent 0 recommends `pause_for_code`, the pipeline MUST halt. The orchestrator reports what is needed and waits for human input. No bypass.
7. **Agent 7 isolation.** The External Auditor receives ONLY the final deliverable and key-info.json. The orchestrator MUST NOT pass intermediate artifacts, factsheets, or review reports to Agent 7.
8. **R14 — Agent self-registration.** Each agent, upon receiving its task, confirms: (a) task understood, (b) inputs accessible, (c) output path confirmed. If any confirmation fails, the agent reports the failure immediately instead of proceeding with incomplete context.
9. **R15 — Auto-announce processing.** Agents report completion status to the orchestrator automatically: `done` (success), `failed` (unrecoverable), or `needs_rework` (partial, fixable). The orchestrator does not poll for status — it waits for the announcement.

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

### 5.8) Relation to ADR-026
This section generalizes the protocol originally defined in ADR-026 (Compartmented Multi-Spawn for Complex Technical Work). ADR-026 remains the decision record; this section is the operational specification.

### 5.9) Lessons from Production (enforceable)

**Evidence base:** var-cambio-icms (14 versions, 8.96/10), lucas-mapa-mental (6 PDF versions, delivered).

#### Visual generation
- **Macro and inline visuals MUST use the same style.** Two visual systems in one document = client rejection (evidence: lucas v3 → client rejected inconsistency).
- **Visual iteration requires human feedback.** Budget 4-6 render→inspect→fix cycles. Automated QA catches structure issues, not aesthetic preferences.
- **matplotlib FancyBboxPatch is the reference style** for box-and-arrow diagrams: rounded corners, colored fills, thick borders, arrows with `-|>`, sans-serif 10-14pt, DPI=300.
- **Emojis don't render in most PDF fonts.** Replace with ASCII markers ([!], [v], [D], [M], [L]) before PDF generation.

#### Data and locale
- **Brazilian locale (comma as decimal separator) breaks naive regex.** When parsing `14,5%`, a greedy `\d[\d,.]*` will eat `14,` as one group and leave `5%` as the next. Fix: require parentheses for absolute+percent format, use `\s+` (not `\s{2,}`) for labels with internal spaces.
- **Color tiers must be based on the PERCENTAGE, not absolute count.** When data has both (e.g., `406 (28.1%)`), color by the percentage.
- **Scraping frequency data is the product differentiator.** Real exam question frequency from QConcursos (or equivalent) is what no generic LLM provides.

#### Delegation
- **Visual generation is NOT delegable to Codex.** Three attempts failed: truncation, wrong style, locale bugs. Opus must own visual quality.
- **Mechanical verification IS delegable** (consistency checks, grep gates, structured reviews). Provide explicit contracts with numbered checks and expected outputs.
- **Agent contracts must include anti-requirements.** What the agent must NOT do is as important as what it must do (e.g., "do NOT state old errors in student material").

#### PDF generation
- **weasyprint over Puppeteer/Chromium.** Puppeteer causes OOM in constrained environments.
- **`replacements.json` as interface** between visual generation and PDF assembly. Decouples the two, allowing stack changes without rewriting the PDF generator.
- **TOC with clickable internal links** (`<a href="#anchor">`) works in weasyprint PDF output.
- **White space residual is a weasyprint limitation.** Acceptable; migration to Typst/LaTeX not justified unless fine flow control is a hard requirement.

#### Correction notes in student material
- **NEVER state "it was X, now Y" in student-facing material.** Students memorize X. State the correct fact directly. Move correction history to the professor's parecer técnico (separate deliverable).

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
