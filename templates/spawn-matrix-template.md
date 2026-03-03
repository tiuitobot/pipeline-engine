# Spawn Matrix Template

> Purpose: execution plan for a sequential multi-agent pipeline.
> Fill all `{PLACEHOLDER}` values before use.

## Column guide
- `#`: Integer execution order (only integer rows are executable by the engine).
- `Step`: Agent role name.
- `Model`: Model/provider used for this step.
- `Timeout`: Max runtime (example: `10 min`).
- `Input paths`: Comma-separated paths read by the step.
- `Output path`: Artifact written by the step.
- `Task`: Concrete instructions for the worker.
- `Acceptance Criteria`: Binary pass/fail conditions.

| # | Step | Model | Timeout | Input paths | Output path | Task | Acceptance Criteria |
|---|------|-------|---------|-------------|-------------|------|---------------------|
| 0 | {STEP_0_NAME} | {MODEL_TIER_ANALYSIS} | 10 min | {PATH_A}, {PATH_B} | outputs/active/metadata/v{N}/{STEP_0_OUTPUT}.md | Analyze the objective and propose execution strategy for `{DOMAIN}`. | Strategy includes options, risks, and explicit proceed/pause recommendation. |
| 1 | {STEP_1_NAME} | {MODEL_TIER_EXTRACTION} | 12 min | outputs/active/metadata/v{N}/{STEP_0_OUTPUT}.md, {REFERENCE_DATA_PATH} | outputs/active/metadata/v{N}/{STEP_1_OUTPUT}.md | Build the source-of-truth artifact from machine-readable inputs. | All critical claims are traceable to reference data. |
| 2 | {STEP_2_NAME} | {MODEL_TIER_REASONING} | 15 min | outputs/active/metadata/v{N}/{STEP_1_OUTPUT}.md | outputs/active/metadata/v{N}/{STEP_2_OUTPUT}.md | Generate ranked insights aligned with target audience. | Every insight includes source references and impact rationale. |
| 3 | {STEP_3_NAME} | {MODEL_TIER_WRITING} | 15 min | outputs/active/metadata/v{N}/{STEP_2_OUTPUT}.md, version-brief.md | outputs/active/metadata/v{N}/{STEP_3_OUTPUT}.md | Draft narrative/report section for `{TARGET_AUDIENCE}`. | Tone and claims comply with version brief and source-of-truth artifacts. |
| 4 | {STEP_4_NAME} | {MODEL_TIER_QA} | 10 min | outputs/active/metadata/v{N}/{STEP_3_OUTPUT}.md, outputs/active/metadata/v{N}/{STEP_1_OUTPUT}.md | outputs/active/metadata/v{N}/{STEP_4_OUTPUT}.md | Review consistency, quality, and unresolved risks. | Report includes severity classification and actionable fixes. |
| 5 | {STEP_5_NAME} | {MODEL_TIER_ASSEMBLY} | 10 min | outputs/active/metadata/v{N}/{STEP_3_OUTPUT}.md, outputs/active/metadata/v{N}/{STEP_4_OUTPUT}.md | outputs/active/{FINAL_ARTIFACT} | Apply approved fixes and assemble final deliverable. | Final artifact produced and all critical review items resolved. |

## Optional non-executable rows
Use non-integer IDs for orchestration notes/checkpoints. The engine ignores them.

| # | Step | Model | Timeout | Input paths | Output path | Task | Acceptance Criteria |
|---|------|-------|---------|-------------|-------------|------|---------------------|
| 3R | Orchestrator Review Checkpoint | n/a | n/a | outputs/active/metadata/v{N}/{STEP_3_OUTPUT}.md | outputs/active/metadata/v{N}/orchestrator_review.md | Record narrative decisions and binding directives. | Review note committed before next dispatch. |
