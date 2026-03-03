#!/usr/bin/env python3
"""Nível 3 — Playbook Checksum Gate.

Validates that playbook files match their registered checksums in
config/playbook_paths.yaml. Detects drift between playbook content
and the registered contract.

Usage:
    python3 scripts/validate_playbook_checksums.py [--update]

Flags:
    --update   Recalculate checksums and write them back to playbook_paths.yaml.
               Use after intentional playbook edits.

Exit codes:
    0  All checksums match (or --update succeeded)
    1  Checksum mismatch detected (drift)
    2  Configuration error (missing file, bad JSON)
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "playbook_paths.yaml"  # JSON despite .yaml extension


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict:
    if not CONFIG.exists():
        print(f"[ERROR] Config not found: {CONFIG}", file=sys.stderr)
        sys.exit(2)
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def save_config(config: dict) -> None:
    CONFIG.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate() -> list[str]:
    config = load_config()
    checksums = config.get("playbook_checksums", {})

    if not checksums:
        print("[WARN] No playbook_checksums in config. Nothing to validate.")
        return []

    failures = []
    for rel_path, expected_hash in checksums.items():
        full_path = ROOT / rel_path
        if not full_path.exists():
            failures.append(f"  MISSING: {rel_path}")
            continue
        actual_hash = sha256_file(full_path)
        if actual_hash != expected_hash:
            failures.append(
                f"  DRIFT: {rel_path}\n"
                f"    expected: {expected_hash[:16]}...\n"
                f"    actual:   {actual_hash[:16]}..."
            )
        else:
            print(f"  [PASS] {rel_path}")

    return failures


def update() -> None:
    config = load_config()
    checksums = config.get("playbook_checksums", {})

    if not checksums:
        print("[WARN] No playbook_checksums in config. Nothing to update.")
        return

    updated = {}
    for rel_path in checksums:
        full_path = ROOT / rel_path
        if not full_path.exists():
            print(f"  [SKIP] {rel_path} — file not found")
            continue
        new_hash = sha256_file(full_path)
        updated[rel_path] = new_hash
        old = checksums[rel_path]
        if new_hash != old:
            print(f"  [UPDATED] {rel_path}: {old[:16]}... → {new_hash[:16]}...")
        else:
            print(f"  [OK] {rel_path}: unchanged")

    config["playbook_checksums"] = updated
    save_config(config)
    print("\n[DONE] Checksums updated in config/playbook_paths.yaml")


def main():
    if "--update" in sys.argv:
        update()
        sys.exit(0)

    print("[PLAYBOOK CHECKSUM GATE]")
    failures = validate()

    if failures:
        print("\n[FAIL] Playbook drift detected:")
        for f in failures:
            print(f)
        print("\nIf the change was intentional, run:")
        print("  python3 scripts/validate_playbook_checksums.py --update")
        sys.exit(1)
    else:
        print("[PASS] All playbook checksums match.")
        sys.exit(0)


if __name__ == "__main__":
    main()
