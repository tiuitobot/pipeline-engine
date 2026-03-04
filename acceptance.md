# acceptance.md — pipeline-engine

## Definition of Done

Pipeline-engine is considered correctly implemented when ALL of the following pass:

### Structural compliance (playbook §1.1)
- [ ] `config/playbook_paths.yaml` exists and all declared paths are valid
- [ ] `problem.md`, `assumptions.md`, `acceptance.md` exist (exploration mode docs)
- [ ] `docs/playbook-universal.md` checksum matches `config/playbook_paths.yaml`
- [ ] `python3 scripts/validate_playbook_checksums.py` exits 0

### Engine functionality
- [ ] `python3 scripts/pipeline_engine.py --init` creates a valid `pipeline-state.json`
- [ ] `python3 scripts/pipeline_engine.py --dispatch` reads spawn-matrix and returns the correct next agent
- [ ] `python3 scripts/pipeline_engine.py --record-completion` updates state correctly
- [ ] `python3 scripts/pipeline_engine.py --status` outputs readable state summary

### Templates completeness
- [ ] All templates in `templates/` contain `{PLACEHOLDER}` tokens (not filled with domain-specific values)
- [ ] `CONTRACT-00-template.md` covers at minimum: R1 (context budget), R2 (agent communication), R3 (sequential dispatch), R4 (failure recovery)
- [ ] `spawn-matrix-template.md` contains all required columns: #, step, model, timeout, input paths, output path, task, acceptance criteria

### Examples validity
- [ ] Each example in `examples/` has: `spawn-matrix.md`, `version-brief.md`, `r10-plugin-config.json`
- [ ] Examples cover at least 2 distinct domains (currently: econometric-report, teaching-materials)

### Usability gate
- [ ] A developer with no prior context can scaffold a new project using only README.md in < 15 minutes
- [ ] No domain-specific assumptions leak from templates or engine code

### Self-compliance
- [ ] This repo follows its own playbook (§2 modes, §3 non-negotiable rules)
- [ ] `key-info.json` reflects current repo state
