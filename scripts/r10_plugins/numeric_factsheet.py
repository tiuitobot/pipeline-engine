"""Econometric-report focused R10a plugin.

Checks:
- NUM-001: numeric consistency between text and reference JSON
- HEDGE-001: hedged language near non-significant p-values
- ASSET-001: referenced local figure/assets resolve on disk
- SEC-001: section references in text match version brief section ids
"""

from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base_plugin import R10Plugin

ASSERTIVE_WORDS = (
    "demonstra",
    "confirma",
    "prova",
    "proves",
    "demonstrates",
    "confirms",
)

HEDGE_WORDS = (
    "sugere",
    "indica tendência",
    "indica tendencia",
    "não rejeita h0",
    "nao rejeita h0",
    "inconclusivo",
    "estatisticamente inconclusivo",
    "suggests",
    "trend",
    "does not reject h0",
    "inconclusive",
)

SECTION_REF_RE = re.compile(r"§\s*(\d+(?:\.\d+)?)")
DECIMAL_RE = re.compile(r"(?<!\d)([+-]?\d+\.\d{2,6})(?!\d)")


class NumericFactsheetPlugin(R10Plugin):
    """Mechanical validations for numeric/econometric style reports."""

    def validate(
        self,
        agent_output_path: str,
        reference_data_path: str,
        agent_number: int,
    ) -> dict[str, Any]:
        output_path = Path(agent_output_path)
        reference_path = Path(reference_data_path)

        if not output_path.exists():
            return self._build_result(
                agent_number=agent_number,
                checks=[],
                errors=[f"agent output does not exist: {output_path}"],
            )

        text = self._load_text(output_path)

        key_info_path = output_path.resolve().parents[2] / "key-info.json" if len(output_path.resolve().parents) >= 3 else Path("key-info.json")
        key_info_data = self._load_json(key_info_path) if key_info_path.exists() else None

        checks: list[dict[str, str]] = []
        all_errors: list[str] = []

        num_status, num_detail, num_errors = self.check_num_consistency(text, reference_path, key_info_data)
        checks.append({"id": "NUM-001", "name": "reference_numeric_consistency", "status": num_status, "detail": num_detail})
        all_errors.extend(num_errors)

        hedge_status, hedge_detail, hedge_errors = self.check_hedged_language(text, reference_path)
        checks.append({"id": "HEDGE-001", "name": "hedged_language", "status": hedge_status, "detail": hedge_detail})
        all_errors.extend(hedge_errors)

        asset_status, asset_detail, asset_errors = self.check_asset_paths(text, output_path)
        checks.append({"id": "ASSET-001", "name": "figure_paths_resolve", "status": asset_status, "detail": asset_detail})
        all_errors.extend(asset_errors)

        sec_status, sec_detail, sec_errors = self.check_section_ids(text, output_path.parent)
        checks.append({"id": "SEC-001", "name": "section_ids_match", "status": sec_status, "detail": sec_detail})
        all_errors.extend(sec_errors)

        return self._build_result(agent_number=agent_number, checks=checks, errors=all_errors)

    @staticmethod
    def _load_text(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _flatten_numeric_values(self, data: Any, path: str = "") -> list[tuple[str, float]]:
        out: list[tuple[str, float]] = []
        if isinstance(data, dict):
            for key, value in data.items():
                child_path = f"{path}.{key}" if path else str(key)
                out.extend(self._flatten_numeric_values(value, child_path))
        elif isinstance(data, list):
            for idx, value in enumerate(data):
                out.extend(self._flatten_numeric_values(value, f"{path}[{idx}]"))
        elif isinstance(data, (int, float)) and not isinstance(data, bool):
            if math.isfinite(float(data)):
                out.append((path or "root", float(data)))
        elif isinstance(data, str):
            for match in DECIMAL_RE.finditer(data):
                try:
                    out.append((path or "root", float(match.group(1))))
                except ValueError:
                    continue
        return out

    def _collect_expected_numbers(self, reference_data: dict[str, Any], key_info: dict[str, Any] | None) -> list[tuple[str, float]]:
        values = self._flatten_numeric_values(reference_data)
        if key_info is not None:
            model_summary = key_info.get("models_summary", {}) if isinstance(key_info, dict) else {}
            values.extend(self._flatten_numeric_values(model_summary, "models_summary"))

        dedup: dict[tuple[str, int], tuple[str, float]] = {}
        for source, value in values:
            if abs(value) < 0.005:
                continue
            key = (f"{value:.4f}", int(round(value * 1000)))
            dedup[key] = (source, value)
        return list(dedup.values())

    @staticmethod
    def _extract_text_decimals(text: str) -> list[float]:
        values: list[float] = []
        for match in DECIMAL_RE.finditer(text):
            try:
                values.append(float(match.group(1)))
            except ValueError:
                continue
        return values

    def check_num_consistency(
        self,
        text: str,
        reference_data_path: Path,
        key_info_data: dict[str, Any] | None,
    ) -> tuple[str, str, list[str]]:
        if not reference_data_path.exists():
            return ("pass", "SKIP: reference data does not exist.", [])

        reference_data = self._load_json(reference_data_path)
        expected = self._collect_expected_numbers(reference_data, key_info_data)
        text_numbers = self._extract_text_decimals(text)

        if not text_numbers:
            return ("pass", "No decimal numbers (2+ places) found in text.", [])

        failures: list[str] = []
        checked = 0
        for value in text_numbers:
            nearest_src = None
            nearest_val = None
            nearest_abs = None
            for source, expected_val in expected:
                abs_diff = abs(value - expected_val)
                if nearest_abs is None or abs_diff < nearest_abs:
                    nearest_abs = abs_diff
                    nearest_val = expected_val
                    nearest_src = source

            if nearest_abs is None or nearest_val is None:
                continue

            checked += 1
            rel_diff = nearest_abs / max(abs(nearest_val), 1e-12)
            if nearest_abs > 0.01 or rel_diff > 0.01:
                failures.append(
                    f"text={value:.6f} diverges from reference={nearest_val:.6f} "
                    f"(src={nearest_src}, abs={nearest_abs:.6f}, rel={rel_diff:.2%})"
                )

        if failures:
            return ("fail", f"{len(failures)}/{max(checked, 1)} numbers diverge beyond tolerance.", failures)

        return ("pass", f"{checked} numbers compared with no relevant divergence.", [])

    def _collect_pvalues(self, data: Any, path: str = "") -> list[tuple[str, float]]:
        out: list[tuple[str, float]] = []
        if isinstance(data, dict):
            for key, value in data.items():
                child_path = f"{path}.{key}" if path else key
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    key_lower = key.lower()
                    if "p" in key_lower and any(tag in key_lower for tag in ("p", "pval", "p_value", "pvalue")):
                        fv = float(value)
                        if 0.0 <= fv <= 1.0:
                            out.append((child_path, fv))
                else:
                    out.extend(self._collect_pvalues(value, child_path))
        elif isinstance(data, list):
            for idx, value in enumerate(data):
                out.extend(self._collect_pvalues(value, f"{path}[{idx}]"))
        return out

    @staticmethod
    def _find_context_windows_for_pvalue(text: str, pvalue: float) -> list[str]:
        windows: list[str] = []
        variants = {f"{pvalue:.1f}", f"{pvalue:.2f}", f"{pvalue:.3f}", f"{pvalue:.4f}"}
        for variant in variants:
            pattern = re.compile(rf"p\s*[=<>]\s*{re.escape(variant)}", re.IGNORECASE)
            for match in pattern.finditer(text):
                start = max(0, match.start() - 140)
                end = min(len(text), match.end() + 140)
                windows.append(text[start:end].lower())
        return windows

    def check_hedged_language(self, text: str, reference_data_path: Path) -> tuple[str, str, list[str]]:
        if not reference_data_path.exists():
            return ("pass", "SKIP: reference data missing; p-value checks not applied.", [])

        reference_data = self._load_json(reference_data_path)
        pvals = self._collect_pvalues(reference_data)
        if not pvals:
            return ("pass", "No p-values found in reference data.", [])

        errors: list[str] = []
        checked = 0
        for source, pvalue in pvals:
            if pvalue <= 0.05:
                continue

            windows = self._find_context_windows_for_pvalue(text, pvalue)
            if not windows:
                continue

            checked += 1
            for window in windows:
                if any(word in window for word in ASSERTIVE_WORDS):
                    errors.append(f"{source} p={pvalue:.4f}: assertive language near non-significant p-value")
                    break

                if pvalue > 0.10 and not any(word in window for word in HEDGE_WORDS):
                    errors.append(f"{source} p={pvalue:.4f}: missing mandatory hedging language")
                    break

        if errors:
            return ("fail", f"{len(errors)} language violations for non-significant results.", errors)

        if checked == 0:
            return ("pass", "No non-significant p-values referenced in text.", [])

        return ("pass", f"{checked} non-significant p-value contexts validated.", [])

    @staticmethod
    def _extract_asset_paths(text: str) -> set[str]:
        refs: set[str] = set()
        for match in re.finditer(r"\b(figures/[\w\-./]+\.(?:png|jpg|jpeg|gif|webp|svg))\b", text, re.IGNORECASE):
            refs.add(match.group(1))

        for match in re.finditer(r"<img[^>]+src=[\"']([^\"']+)[\"']", text, re.IGNORECASE):
            src = match.group(1).strip()
            if any(src.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
                refs.add(src)

        return refs

    @staticmethod
    def _resolve_asset_path(asset_ref: str, figures_base: Path, output_dir: Path) -> Path | None:
        if asset_ref.startswith(("http://", "https://", "data:")):
            return None
        if os.path.isabs(asset_ref):
            return Path(asset_ref)
        if asset_ref.startswith("figures/"):
            return figures_base / asset_ref.split("figures/", 1)[1]
        return (output_dir / asset_ref).resolve()

    def check_asset_paths(self, text: str, agent_output_path: Path) -> tuple[str, str, list[str]]:
        refs = self._extract_asset_paths(text)
        if not refs:
            return ("pass", "No asset/figure references found.", [])

        repo_root = self._find_repo_root(agent_output_path)
        figures_base = repo_root / "outputs" / "active" / "figures"

        missing: list[str] = []
        checked = 0
        for ref in sorted(refs):
            resolved = self._resolve_asset_path(ref, figures_base, agent_output_path.parent)
            if resolved is None:
                continue
            checked += 1
            if not resolved.exists():
                missing.append(f"referenced asset does not exist: {ref} -> {resolved}")

        if missing:
            return ("fail", f"{len(missing)} unresolved assets.", missing)

        return ("pass", f"{checked} assets resolved successfully.", [])

    @staticmethod
    def _extract_section_ids(text: str) -> set[str]:
        return {match.group(1) for match in SECTION_REF_RE.finditer(text)}

    def check_section_ids(self, text: str, output_dir: Path) -> tuple[str, str, list[str]]:
        refs = self._extract_section_ids(text)
        if not refs:
            return ("pass", "No section references (§N) found.", [])

        brief_path = self._infer_version_brief(output_dir)
        if brief_path is None:
            return ("pass", "Could not infer version-brief path from output directory.", [])

        if not brief_path.exists():
            return ("pass", f"version-brief not found ({brief_path}); permissive mode.", [])

        allowed = self._extract_section_ids(self._load_text(brief_path))
        if not allowed:
            return ("pass", "No extractable section IDs in version brief.", [])

        invalid = sorted(ref for ref in refs if ref not in allowed)
        if invalid:
            return (
                "fail",
                f"{len(invalid)} section references are outside version-brief catalog.",
                [f"section reference not in version-brief: §{ref}" for ref in invalid],
            )

        return ("pass", f"{len(refs)} section references validated against version-brief.", [])

    @staticmethod
    def _find_repo_root(start_path: Path) -> Path:
        cur = start_path.resolve()
        for path in [cur] + list(cur.parents):
            if (path / ".git").exists() or (path / "key-info.json").exists():
                return path
        return Path.cwd()

    def _infer_version_brief(self, output_dir: Path) -> Path | None:
        base = output_dir.name
        match = re.match(r"v\d+", base)
        if not match:
            return None
        repo_root = self._find_repo_root(output_dir)
        return repo_root / "plans" / f"{match.group(0)}-agents" / "version-brief.md"

    @staticmethod
    def _build_result(agent_number: int, checks: list[dict[str, str]], errors: list[str]) -> dict[str, Any]:
        passed = sum(1 for check in checks if check["status"] == "pass")
        total = len(checks)
        return {
            "agent": agent_number,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "PASS" if not errors else "FAIL",
            "checks": checks,
            "errors": errors,
            "summary": f"{passed}/{total} checks passed",
        }
