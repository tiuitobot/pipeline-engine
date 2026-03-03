# CONTRACT-00 — Orchestrator ({ORCHESTRATOR_MODEL})

## Purpose
Define hard constraints for the orchestrator session during multi-agent {DOMAIN} pipeline execution.
This contract protects context budget, enforces sequential discipline, and prevents the "orchestrator-becomes-executor" anti-pattern.

> **Operational note (current mode):** set fallback routing for pipeline agents according to your environment policy.

## Scope
Applies whenever the Multi-Agent Pipeline for `{DOMAIN}` deliverables (Universal §5 / Repo §9) is active.

> Replace all `{PLACEHOLDER}` tokens with your project-specific values before activating this contract.


---

## Hard Rules (violação = pipeline inválido)

### R1. Context Budget — Never Read Data Files
The orchestrator MUST NOT read data files (JSON, CSV, HTML >1KB) into its own context.
- **Allowed:** Read file structure (first 30 lines), headers, keys.
- **Forbidden:** Read full `{REFERENCE_DATA}` files, full HTML, full CSV, model outputs.
- **Rationale:** Each agent reads what it needs. Orchestrator stays lean (~2K tokens per step).

### R2. Agent Communication — Return Messages Only
The orchestrator receives from each agent ONLY:
- Status: "done" / "failed" / "needs rework"
- Output path: where the agent wrote its artifact
- Brief summary: 1-3 sentences max
- Issues found: count + severity (if reviewer)

**No file content in return messages.** Artifacts stay on disk.

### R3. Sequential Dispatch — One Agent at a Time
- Spawn Agent N → wait for completion → evaluate return → spawn Agent N+1
- No parallel spawns within the pipeline (rate limit protection + dependency chain)
- Exception: independent scouts (e.g., web research) may run parallel to pipeline

### R4. Failure Recovery — Re-delegate, Never Absorb
When an agent fails (timeout, bad output, crash):
1. **First attempt:** Re-spawn same agent with refined instructions
2. **Second attempt:** Re-spawn in **codex fallback mode** (or keep codex when already in codex)
3. **Third attempt:** Spawn with simplified task (split into sub-tasks), still in codex fallback mode
4. **NEVER:** Pull the agent's work into the orchestrator context

### R5. Polling Discipline
- Timeout hard: 5 minutes per agent (configurable in spawn-matrix)
- Poll interval: 30 seconds
- Max polls: 10 per agent
- If timeout: kill → follow R4 failure recovery

### R6. Accumulation Path
All agent outputs MUST be written to the repo's canonical output tree:
```
outputs/active/metadata/v{N}/   # intermediate artifacts (factsheet, insights, sections, review)
outputs/active/report_executive/ # final assembled executive report (HTML, PDF)
outputs/active/report_technical/ # final assembled technical report (if applicable)
plans/<version>-agents/          # planning only (spawn-matrix, version-brief) — NOT agent outputs
```
Each agent reads from and writes to `outputs/active/metadata/v{N}/`. Orchestrator never relays content between agents.
Planning artifacts (spawn-matrix, version-brief) stay in `plans/` — they are inputs, not outputs.

### R7. Spawn Matrix Before Execution
Before spawning Agent 1, the orchestrator MUST have a `spawn-matrix.md` with:
- Agent order, model, timeout, input paths, output paths, acceptance criteria
- This is the execution plan. No ad-hoc spawning.

### R8. Orchestrator QA Gate — Final Quality Review + Narrative Coherence
After Agent 5 (Consistency Reviewer) and BEFORE Agent 6 (Assembler), the orchestrator MUST perform a quality review.

> **Note:** When Agent 7 (External Auditor) is active, R8 also gates the transition from Agent 6 → Agent 7. If Agent 7 returns FAIL, the orchestrator triggers rework via R4 and re-runs the affected agent(s) before re-submitting to Agent 7. This is NOT delegated — the orchestrator is the final judge of whether the output matches the intended purpose.

**What to check:**
- version-brief.md compliance: every feedback item (W1-W4) addressed
- Hedged language: non-significant results (p > 0.05) use cautious wording
- Tone: appropriate for target audience (read as if the stakeholder is reading for the first time)
- Numerical consistency: spot-check 3+ numbers against `{REFERENCE_DATA}`
- **Narrative coherence (cross-model):** The orchestrator MUST verify that interpretations across models are consistent and non-contradictory. The orchestrator is the only entity with user conversation context (design decisions, interpretation nuances). If contradictions exist, the orchestrator rewrites the affected sections directly (exception to R4 for narrative-only edits) or sends rework with specific reconciliation instructions.

**How to check (R1 compliant):**
- Read `review_report.md` from Agent 5 (small file, allowed)
- Use grep/python for spot checks on section files (NOT reading full content into context)
- Reference version-brief.md sections (already known from orchestration)

**If any check fails:**
- Send rework feedback to the responsible agent (R4 applies — do NOT fix it yourself)
- Do NOT proceed to Agent 6 until all checks pass

**Full checklist:** See `spawn-matrix.md` Step 5.5 for project-specific QA checklist.

### R9. Incremental-First — Always Start from Previous Version
The pipeline MUST start from the previous version's output (`v{N-1}`) as base, NOT from scratch.
- **Assembler (Agent 6)** receives `v{N-1}.html` as mandatory input and applies surgical changes.
- **All agents** receive the previous version's structure as context for what to preserve.
- **Rewrite from scratch** requires explicit user instruction (e.g., "start fresh", "from scratch").
- **Rationale:** Previous versions contain accumulated richness (graphs, tables, formatting, narrative flow) that is expensive to regenerate. Incremental evolution preserves this investment.
- **Gate:** `spawn-matrix.md` MUST list `v{N-1}` artifact path in Agent 6 input. Orchestrator blocks assembly if missing.

### R10. Orchestrator Review — Post-Agent Artifact Enrichment (Split: Mechanical + Narrative)

R10 has two components that run sequentially after each agent completes:

#### R10a. Mechanical Validation (script, non-LLM)
- Run your configured R10a mechanical validator (example: `scripts/validate_r10a.py --plugin {R10_PLUGIN}`) against the agent's output
- Checks: numerical consistency reference-data↔text, hedged language for non-significant results, figure/asset paths resolve, section IDs match catalog
- Output: `r10_mechanical_{agent_N}.json` (pass/fail per item)
- Time: <30 seconds
- **Gate:** If any FAIL item → automatic rework to same agent with specific error list (no orchestrator tokens spent)

#### R10b. Narrative Review (Orchestrator LLM)
After R10a passes, the orchestrator MUST:
1. **Read** `r10_mechanical_{agent_N}.json` (confirms pass)
2. **Review** the agent's output for accuracy, gaps, and alignment with user conversation context
3. **Append** an "§ Orchestrator Review" section to the agent's output file with:
   - Verdicts on any tensions/contradictions identified (reconciled or real)
   - Data correction alerts (with SSOT reference)
   - Binding directives for downstream agents
   - Emphasis on critical points that must not be lost
4. **Commit** the enriched file before spawning the next agent

**Rationale:** The orchestrator is the only entity with full user conversation context (design decisions, interpretation nuances, corrections discussed in chat). Without R10, downstream agents miss orchestrator-level insights and corrections that were only discussed in chat but never written to artifacts. The mechanical/narrative split saves orchestrator tokens on deterministic checks.

**What triggers R10:** Every agent completion. Even if no corrections are needed, append a minimal "§ Orchestrator Review: Approved without changes" to maintain audit trail.

**Gate:** Next agent spawn is blocked until R10a passes AND orchestrator review is committed to the previous agent's output file.

---

### R11. Agent 0 Decision Gate — Proceed or Pause for Code
After Agent 0 (Domain Specialist) completes `research_proposals.md`, the orchestrator MUST:
1. **Read** the proposals and their `pause_for_code` / `proceed` recommendation
2. **Decide:**
   - `proceed` → Agent 1 receives expanded scope, pipeline continues normally
   - `pause_for_code` → orchestrator creates checkpoint (`git commit "checkpoint: pre-agent0-exploration-{desc}"`), spawns Codex with spec, validates result, rollbacks on failure
3. **Gate:** Agent 1 MUST NOT be spawned until Agent 0's gate decision is resolved

**Rationale:** Agent 0 may identify high-impact improvements that require new code (gates, scripts, data transformations). The decision gate prevents the pipeline from proceeding with stale capabilities when code exploration could yield better results.

**Rollback:** If code exploration fails (`pipelines/pipeline.py --strict` or validations fail), `git checkout checkpoint` and pipeline continues without exploration. Exploration output is an **annexe** — it does not block the main report if it fails.

### R12. Post-Audit Triage — Recommendation-by-Recommendation Decision Protocol
After Agent 7 (External Auditor) delivers its scored audit, the orchestrator MUST NOT blindly accept or reject the verdict. Instead:

1. **Enumerate** every finding (🔴/🟡/🟢) from the audit report
2. **For each finding**, decide one of:
   - ✅ **Accept & fix** — finding is valid, determine fix type (see step 3)
   - ❌ **Reject with justification** — finding is incorrect or out of scope (document why)
   - ⏸️ **Defer to v{N+1}** — valid but requires data/code not available now (document explicitly)
3. **Classify fix type** for accepted findings:
   - **Pontual (HTML edit):** text, formatting, labels, missing sentences → delegate to Agent 6 rework
   - **Agent re-run:** finding requires regenerating an agent's full output (e.g., Agent 4 Technical Writer missed a model section) → re-spawn that agent with specific instructions
   - **Pipeline re-run:** finding invalidates a foundational artifact (e.g., factsheet has wrong data, model was misspecified) → full pipeline re-execution from affected step
4. **Write triage table** to `outputs/active/metadata/v{N}/audit_triage.md` with columns: Finding ID | Severity | Decision | Fix Type | Responsible | Status
5. **Execute fixes** grouped by type (all pontual fixes in one rework spawn, agent re-runs sequentially)
6. **Re-run Agent 7** after ALL fixes applied — the re-audit MUST receive:
   - The updated HTML (post-fixes)
   - The factsheet SSOT (unchanged unless factsheet was also fixed)
   - The **previous audit report** (`audit_v{N}_scored.md`) — so the auditor can verify each prior finding was addressed and score convergence
   - The audit score is only final after re-audit confirms fixes
7. **Gate:** Pipeline CANNOT be marked complete until Agent 7 returns PASS or CONDITIONAL PASS with no remaining 🔴

**Decision criteria for "pipeline re-run":**
- Any `{REFERENCE_DATA}` value found incorrect against source data → pipeline re-run from Agent 1
- Any model specification error (wrong lag, wrong variable) → pipeline re-run from Agent 0
- Narrative-only issues (language, structure, missing caveats) → NEVER pipeline re-run

**Anti-pattern: bulk-accept** — accepting all findings without per-finding evaluation. Each finding deserves individual assessment because auditor can be wrong (false positives, different conventions, missing context about domain decisions).

### R14. Agent Self-Registration in Pipeline State
Each agent MUST update `pipeline-state.json` as part of its own commit, BEFORE the orchestrator processes R10a/R10b. This enables the watchdog to detect completion independently of orchestrator processing.

**Mandatory instruction appended to every agent spawn contract:**
```
### Pipeline State Update (mandatory, do this BEFORE your git commit)
python3 scripts/update_pipeline_state.py outputs/active/metadata/v{N}/ {agent_number} "{agent_name}" {model} {thinking} done pending
```

**Rationale:** Orchestrator updating state after processing creates a circular dependency — the watchdog only sees the gap after the orchestrator already processed it. Agent self-registration breaks this cycle: agent completes → updates state → watchdog sees `r10a_status: pending` → nudges orchestrator if R10a not processed within poll interval.

---

### R15. Auto-Announce Processing Protocol
When a subagent auto-announce message arrives (format: `✅ Subagent {label} finished`), the orchestrator MUST **immediately** execute the following sequence — no user prompt required:

1. `git pull --ff-only` to sync agent's commit
2. Run R10a mechanical validation (`validate_r10_checklist.py`)
3. Update pipeline-state with R10a result
4. Write R10b binding directives if applicable
5. Commit + push state updates
6. Dispatch next agent in sequence

**Enforcement analogy:** This rule mirrors heartbeat processing — heartbeat arrives → read HEARTBEAT.md → execute protocol. Auto-announce arrives → read R15 → execute pipeline continuation. Same trigger-contract-action pattern.

**Anti-pattern: wait-for-user-nudge** — Auto-announce arrived but orchestrator waits for user to say "agent X chegou" before processing. This defeats pipeline autonomy and makes the user a manual scheduler.

---

### R13. Changelog Appendix — Post-Audit Version Diff
After Agent 7 delivers final PASS (or CONDITIONAL PASS with no remaining 🔴), the orchestrator MUST generate a changelog appendix comparing v{N} against v{N-1}:

1. **When:** After pipeline completion (post-Agent 7 final verdict), before PDF generation
2. **What:** Structured diff covering:
   - **Sections added/removed/modified** (list by h2/h3 heading)
   - **Numerical corrections** (old value → new value, with source reference)
   - **Methodological changes** (new models, changed specifications, new tests)
   - **Narrative changes** (reframed interpretations, new caveats, audience adjustments)
   - **Structural/formatting changes** (TOC added, CSS changes, new figures)
   - **Audit score** (v{N} score vs v{N-1} score, if available)
3. **How:** Orchestrator spawns a dedicated agent (any model) with:
   - Input: `v{N}.html` + `v{N-1}.html` + `factsheet v{N}` + `factsheet v{N-1}` (if exists)
   - Output: `outputs/active/metadata/v{N}/changelog_v{N}_vs_v{N-1}.md`
4. **Integration:** The changelog is appended to the final HTML as a collapsible `<details>` section at the end (before closing `</body>`), titled "Anexo: Registro de Alterações (v{N} vs v{N-1})"
5. **PDF:** Changelog appears as last appendix in the PDF

**Rationale:** The stakeholder reviewer ({STAKEHOLDER_REVIEWER}) needs to know what changed without reading the entire deliverable. Executive reviewers ({STAKEHOLDER_EXECUTIVE}) may want to verify specific corrections. This closes the traceability loop from feedback → fix → verification.

**Gate:** Pipeline log MUST record changelog generation. PDF MUST NOT be generated before changelog is appended to HTML.

### R16. Deferred Issues → Backlog (mandatory)
After Agent 7 audit triage (R12), any finding classified as ⏸️ **Defer to v{N+1}** MUST be added to `backlog/backlog.md` with:
- Unique ID (`BL-REP-xxx`)
- Description of the finding
- Source reference (audit report, issue number)
- Concrete next action

**Rationale:** Deferred findings that live only in audit reports get lost between versions. The backlog is the canonical source of work items (per {PROJECT_OWNER} directive). Pipeline completion gate MUST verify that every ⏸️ finding has a corresponding backlog entry.

**Anti-pattern: defer-and-forget** — marking findings as "next version" without creating a trackable work item. Without backlog entry, the issue is effectively abandoned.

---

## Soft Guidelines (recomendações operacionais)

### G1. Progress Updates
For pipelines with 3+ agents, send {PROJECT_OWNER} a brief status after each agent completes:
"Agent 2/6 done — insights.md written, 4 findings. Next: Executive Writer."

### G2. Pre-flight Check
Before starting pipeline:
- [ ] All input files exist (data JSONs, CSVs)
- [ ] Accumulation directory created
- [ ] spawn-matrix.md written and reviewed
- [ ] Previous run artifacts archived or cleaned

### G3. Post-pipeline Commit
Single atomic commit after pipeline completes (not per-agent).
Format: `pipeline: v{N} {DOMAIN} deliverable ({model_count} models, {section_count} sections)`

---

## Enforcement

### Gate: `scripts/validate_orchestrator_contract.sh`
Checks before pipeline start:
- [ ] spawn-matrix.md exists with required fields
- [ ] accumulation directory exists
- [ ] input files referenced in spawn-matrix exist

### Audit trail
After pipeline completes, orchestrator writes `plans/<project>/pipeline-log.md`:
- Timestamp per agent (start, end, status)
- Tokens consumed in orchestrator context (estimated)
- Failures and recovery actions taken

---

## Anti-patterns (named, for signal capture)

| Anti-pattern | Description | Violated Rule |
|-------------|-------------|---------------|
| **orchestrator-becomes-executor** | Agent fails → orchestrator absorbs work into own context | R4 |
| **fat-orchestrator** | Orchestrator reads full data files | R1 |
| **polling-tornado** | 40+ polls without timeout discipline | R5 |
| **content-relay** | Orchestrator reads file A, passes content to Agent B via prompt | R2, R6 |
| **ad-hoc-spawn** | No spawn-matrix, agents spawned reactively | R7 |
| **tabula-rasa** | Pipeline generates report from scratch ignoring v{N-1} richness (graphs, tables, formatting) | R9 |
| **narrative-silo** | Each agent writes interpretation in isolation; contradictions between models go undetected | R8 |
| **chat-only-review** | Orchestrator discusses corrections in chat but never writes them into artifacts; downstream agents miss context | R10 |
| **bulk-accept-audit** | Orchestrator accepts all Agent 7 findings without per-finding triage; misses false positives and wastes rework on invalid findings | R12 |
| **audit-then-ship** | Orchestrator applies fixes but skips re-audit; final score doesn't reflect actual state of report | R12 |
| **silent-evolution** | New version delivered without explicit changelog; reader must diff manually to understand what changed | R13 |
| **defer-and-forget** | Audit findings deferred to "next version" but never added to backlog; effectively abandoned | R16 |
