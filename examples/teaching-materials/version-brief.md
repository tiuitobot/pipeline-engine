# Version Brief — Teaching Materials (Concurso Mind Maps)

> Based on real production: lucas-mapa-mental (2026-03-06).

## §A. Context
- **Domain:** Concurso preparation materials (any legal/technical discipline)
- **Audience:** Students preparing for competitive exams (via professor)
- **Goal:** Transform professor's class material into structured mind maps with:
  - Real exam frequency data (scraped from QConcursos or equivalent)
  - Factual corrections verified against legislation
  - Visual diagrams (flowcharts, bar charts, tables, hierarchies)
  - Professional PDF with TOC and unified visual identity

## §B. Inputs Required
1. **Source material** (`data/source-material.txt`) — professor's class notes, slides, or transcript
2. **Frequency data** (`data/frequency-external.json`) — scraped from exam question bank
3. **Detailed questions** (`data/questions-detailed.json`) — 200+ questions with concept tags (optional, enriches analysis)

## §C. Outputs
1. **PDF mind maps** — for students (via professor). N maps with visual diagrams, frequency markers, mnemonics.
2. **PDF parecer técnico** — for professor only. Factual errors, omissions, outdated legislation.
3. **corrections.json** — machine-readable substitution pairs for audit trail.

## §D. Key Constraints
- Solo-First (§5.0): Agents 0+1 must be Opus solo before multi-agent activation
- Visual generation: Opus only (3 Codex attempts failed in production)
- Scraping: main session only (not delegable — requires judgment for anti-bot bypass)
- Locale: Brazilian Portuguese (comma decimal separator, specific legal terminology)
- PDF: weasyprint (Puppeteer/Chromium causes OOM)
- Correction notes: NEVER state old errors in student material

## §E. Graduation Criteria for Multi-Agent (§5.0)
- [x] v1 PDF delivered and reviewed by human
- [x] Document exceeds single-context threshold (>30 pages)
- [x] Iterative corrections stabilized
→ Agents 2-5 activated after Agent 1 delivery

## §F. Visual Stack
- **Flowcharts/hierarchies/boxes:** matplotlib FancyBboxPatch (PNG, 300dpi)
- **Bar charts:** seaborn with red/gold/green tiers by percentage
- **Tables:** HTML native (weasyprint renders better than PNG)
- **Palette:** navy=#1a237e, red=#c62828, gold=#f9a825, green=#2e7d32, blue=#1565c0, purple=#6a1b9a
- **Interface:** `replacements.json` decouples visual generation from PDF assembly
