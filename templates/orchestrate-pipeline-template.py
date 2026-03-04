#!/usr/bin/env python3
"""
orchestrate_pipeline.py — Project-specific pipeline entry point (TEMPLATE)

⚠️  TEMPLATE — substitute all {PLACEHOLDER} tokens before use.
    This script is the ONLY entry point for pipeline runs in your project.

Architecture:
    This is a thin wrapper around pipeline_engine.py that adds:
    (1) Pre-flight input validation gate (project-specific required files)
    (2) Knowledge briefing validation (if using EPIC/memory context)
    (3) A single entry point that enforces CONTRACT-00 compliance

    The engine itself (pipeline_engine.py) handles:
    - Spawn matrix parsing
    - Pipeline state management (pipeline-state.json SSOT)
    - Agent dispatch sequencing
    - R10a recording and blocking
    - R11 Agent 0 gate (proceed / pause_for_code)

Usage (same interface as pipeline_engine.py):
    python3 scripts/orchestrate_pipeline.py \\
        --accumulation-dir outputs/active/metadata/{VERSION} \\
        --init

    python3 scripts/orchestrate_pipeline.py \\
        --accumulation-dir outputs/active/metadata/{VERSION} \\
        --dispatch

    python3 scripts/orchestrate_pipeline.py \\
        --accumulation-dir outputs/active/metadata/{VERSION} \\
        --dry-run

See pipeline_engine.py --help for all available flags.
"""

import os
import sys

# ─── Project-specific: required repo-level files ──────────────────────────────
# Add or remove entries as needed. These are checked BEFORE any agent spawn.
# Format: { "label": "relative/path/from/repo/root" }

REQUIRED_INPUTS = {
    "contract":       "docs/contracts/CONTRACT-00-orchestrator.md",
    "playbook":       "docs/playbook-universal.md",
    "key_info":       "key-info.json",
    # Add project-specific required files here:
    # "domain_config": "{PLACEHOLDER_PATH}",
}

# ─── Project-specific: required accumulation-dir files ────────────────────────
# These files must exist in --accumulation-dir before the pipeline starts.

ACCUMULATION_INPUTS = {
    "spawn_matrix":   "spawn-matrix.md",
    "version_brief":  "version-brief.md",
    # Optional: knowledge briefing (comment out if not using EPIC/memory context)
    # "knowledge_briefing": "knowledge_briefing.md",
}

# ─── Optional: knowledge briefing section validation ──────────────────────────
# If knowledge_briefing.md is required, define which sections must be present.
# Comment out or set to [] to skip section validation.

KNOWLEDGE_BRIEFING_SECTIONS: list[str] = [
    # "## Patterns",
    # "## Signals",
    # "## Tech KB",
]

# ─── Gate: validate all inputs ────────────────────────────────────────────────

def validate_inputs(repo_root: str, accumulation_dir: str) -> list[str]:
    """
    Check that all required files exist before any agent spawn.
    Returns list of blocking errors (empty = pass).
    """
    errors = []

    for label, rel_path in REQUIRED_INPUTS.items():
        full = os.path.join(repo_root, rel_path)
        if not os.path.exists(full):
            errors.append(f"MISSING: {rel_path} ({label})")

    for label, filename in ACCUMULATION_INPUTS.items():
        full = os.path.join(accumulation_dir, filename)
        if not os.path.exists(full):
            errors.append(f"MISSING in accumulation-dir: {filename} ({label})")

    kb_filename = ACCUMULATION_INPUTS.get("knowledge_briefing")
    if kb_filename and KNOWLEDGE_BRIEFING_SECTIONS:
        kb_path = os.path.join(accumulation_dir, kb_filename)
        if os.path.exists(kb_path):
            content = open(kb_path, encoding="utf-8").read()
            for section in KNOWLEDGE_BRIEFING_SECTIONS:
                if section not in content:
                    errors.append(
                        f"INCOMPLETE knowledge_briefing.md: missing section '{section}'"
                    )

    return errors


# ─── Entrypoint ───────────────────────────────────────────────────────────────

def main() -> int:
    # Detect --accumulation-dir and --repo-root from argv without full argparse
    # (avoids duplicating argument definitions from pipeline_engine.py)
    accumulation_dir = "."
    repo_root = "."
    dry_run = "--dry-run" in sys.argv

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--accumulation-dir" and i < len(sys.argv):
            accumulation_dir = sys.argv[i + 1]
        if arg == "--repo-root" and i < len(sys.argv):
            repo_root = sys.argv[i + 1]

    repo_root = os.path.abspath(repo_root)
    accumulation_dir = os.path.abspath(accumulation_dir)

    # Run pre-flight gate
    errors = validate_inputs(repo_root, accumulation_dir)
    if errors:
        print("=" * 60)
        print("PIPELINE BLOCKED — required inputs missing or incomplete:")
        print("=" * 60)
        for e in errors:
            print(f"  ✗ {e}")
        print()
        print("Fix the above before running the pipeline.")
        print("Gate: orchestrate_pipeline.py validate_inputs()")
        return 2

    if dry_run:
        print("[DRY RUN] All inputs validated. Pipeline not started.")
        return 0

    # Delegate to pipeline_engine.py (same interface, full engine logic)
    engine_path = os.path.join(os.path.dirname(__file__), "pipeline_engine.py")
    if not os.path.exists(engine_path):
        print(f"ERROR: pipeline_engine.py not found at {engine_path}")
        return 1

    import subprocess
    result = subprocess.run(
        [sys.executable, engine_path] + sys.argv[1:],
        cwd=repo_root,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
