# Spawn Matrix — Teaching Materials (Concurso Mind Maps)

> Based on real production: lucas-mapa-mental (2026-03-06), 7 agents, PDF v6 delivered.
> Solo-First (§5.0) was followed: Agents 0+1 by Opus solo, then multi-agent for 2-5.

| # | Agent | Model | Input | Output | Task | Acceptance Criteria | Notes |
|---|-------|-------|-------|--------|------|---------------------|-------|
| 0 | Domain Analyst (Parecer) | opus | `data/source-material.txt`, `data/frequency-external.json` | `outputs/active/parecer-tecnico.md`, `outputs/active/corrections.json` | Analyze source material for factual errors, omissions, outdated legislation. Cross-reference with external frequency data. Generate machine-readable corrections. | (1) Every error has severity + exact fix. (2) corrections.json has substitution pairs. (3) Web-verified critical claims. (4) Separate deliverable for professor (not students). | **Solo phase.** Opus main. Requires domain judgment + web verification. NOT delegable. |
| 1 | Content Producer (Mind Maps) | opus | `outputs/active/corrections.json`, `data/frequency-external.json`, `data/questions-detailed.json` | `outputs/active/mind-map-specs/*.md` (N files) | Produce N structured mind maps in MD. Apply corrections. Integrate frequency data with priority markers. Template: high-frequency → traps → rules+exceptions → exam data → mnemonics. | (1) N files exist with template sections. (2) All corrections applied. (3) Frequency data from real sources, not invented. (4) No residual prohibited terms (grep gate). | **Solo phase.** Opus main. Number of maps = structure of subject. |
| 2 | Macro Visual Generator | opus | `outputs/active/mind-map-specs/*.md`, `data/questions-detailed.json` | `outputs/active/visuals/*.png` (1 per topic) | Generate 1 macro diagram per topic. matplotlib FancyBboxPatch style: rounded corners, colored fills (#c62828/#f9a825/#2e7d32/#1565c0), thick borders, arrows -|>, sans-serif 10-14pt, DPI=300. | (1) All PNGs render at 300dpi. (2) Fit A4 portrait (174mm x 261mm usable). (3) Visual style matches inline visuals. (4) Manifest with SHA256 hashes. | Opus solo. Visual quality requires iterative judgment. |
| 2B | Inline Visual Generator | opus | `outputs/active/mind-map-specs/*.md` | `outputs/active/visuals/inline-v3/` + `replacements.json` | Convert ALL ASCII code blocks in MDs to styled PNGs/HTML. Classify: flowchart→matplotlib, bar→seaborn, table→HTML, hierarchy→matplotlib, box→matplotlib. Same FancyBboxPatch style as macro. | (1) 100% blocks converted. (2) Colors match macro palette. (3) Bar chart percentages verified (locale-aware regex). (4) replacements.json maps source:seq → output. | **NOT delegable to Codex.** 3 attempts failed (truncation, wrong style). Regex with Brazilian locale (comma decimal) requires careful testing. |
| 3 | Consistency Reviewer | codex | `outputs/active/corrections.json`, `outputs/active/mind-map-specs/*.md`, `data/source-material.txt` | `outputs/active/metadata/consistency-review.json` | Cross-check: (1) All corrections applied? (2) Frequency data matches source? (3) No prohibited terms? (4) Legal citations correct? | (1) PASS/FAIL/WARN per check. (2) Machine-readable JSON. (3) Any FAIL = pipeline blocks until fixed. | Delegable. Mechanical verification. Contract with explicit checks. |
| 4 | Final Reviewer | codex | `outputs/active/mind-map-specs/*.md`, `outputs/active/metadata/consistency-review.json` | `outputs/active/metadata/final-review.json` | Final quality gate: (1) Grep prohibited terms. (2) Spot-check legal citations. (3) Verify didactic quality. (4) Flag dangerous "correction notes" (stating old errors makes students memorize them). | (1) Verdict: PASS or NEEDS_FIXES with actionable items. (2) Grep of prohibited terms = zero hits. (3) No "was X, now Y" patterns in student material. | Delegable. Provide explicit contract with 6+ verification types. Opus applies fixes from review. |
| 5 | Visual QA Reviewer | sonnet | Rendered PDF pages (PNG via PyMuPDF) | `outputs/active/metadata/visual-qa-review.json` | Review ~25% of PDF pages (sampled uniformly). Score 6 dimensions 1-10: visual identity, legibility, layout, diagram quality, study usability, technical issues. | (1) JSON with per-dimension scores + overall. (2) Verdict: PASS or NEEDS_FIXES. (3) Specific page references for issues. | Delegable to Sonnet. Feeds iteration cycle. |

## Post-pipeline: Visual Iteration (Opus, NOT delegable)

After Agent 5, Opus enters render→inspect→fix cycle:
1. Render PDF pages via PyMuPDF
2. Inspect via vision model (image tool)
3. Fix scripts and regenerate
4. Repeat until client approves

**Typical: 4-6 iterations** (evidence: lucas-mapa-mental v1→v6).

## Deliverables

| # | Artifact | Audience | Format |
|---|----------|----------|--------|
| 1 | Mind maps PDF | Students (via professor) | PDF with TOC + diagrams |
| 2 | Parecer técnico PDF | Professor only | PDF with corrections report |
| 3 | corrections.json | Machine audit | JSON with substitution pairs |
| 4 | Manifests | Internal audit | JSON with SHA256 hashes |
