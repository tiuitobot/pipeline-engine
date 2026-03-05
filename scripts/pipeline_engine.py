#!/usr/bin/env python3
"""Generic multi-agent pipeline engine.

This module provides a domain-agnostic engine to orchestrate sequential pipelines
from a markdown spawn-matrix and a JSON state file.

Supported CLI operations:
- --init
- --dispatch
- --record-completion
- --record-r10a
- --set-worker / --get-worker
- --status

The engine is intentionally generic and does not embed domain-specific logic.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BLOCKED = 2


@dataclass
class EngineConfig:
    accumulation_dir: Path
    state_filename: str = "pipeline-state.json"


class PipelineEngine:
    """Stateful, sequential pipeline orchestrator.

    The engine reads execution steps from `spawn-matrix.md` and stores runtime
    state in `pipeline-state.json`.
    """

    REQUIRED_COLUMNS = [
        "#",
        "step",
        "model",
        "timeout",
        "input paths",
        "output path",
        "task",
        "acceptance criteria",
    ]

    def __init__(self, accumulation_dir: str | Path, state_filename: str = "pipeline-state.json") -> None:
        self.config = EngineConfig(accumulation_dir=Path(accumulation_dir).resolve(), state_filename=state_filename)

    @property
    def accumulation_dir(self) -> Path:
        return self.config.accumulation_dir

    @property
    def state_path(self) -> Path:
        return self.accumulation_dir / self.config.state_filename

    @staticmethod
    def now_iso() -> str:
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _infer_version(accumulation_dir: Path) -> str:
        base = accumulation_dir.name
        return base if re.fullmatch(r"v\d+", base) else "unknown"

    @staticmethod
    def _parse_timeout_minutes(raw: str) -> int:
        match = re.search(r"(\d+)", raw or "")
        return int(match.group(1)) if match else 5

    @staticmethod
    def _split_input_paths(raw: str) -> list[str]:
        if not raw:
            return []
        parts = re.split(r"\s*,\s*|\s*;\s*|\s+\+\s+", raw.strip())
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def _save_json(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    def parse_spawn_matrix(self, spawn_matrix_path: str | Path | None = None) -> list[dict[str, Any]]:
        """Parse spawn-matrix markdown table into executable agent steps.

        Only rows with integer values in the `#` column are treated as executable
        steps. Rows like `1R` or `2.5` are ignored.
        """
        matrix_path = Path(spawn_matrix_path) if spawn_matrix_path else self.accumulation_dir / "spawn-matrix.md"
        lines = matrix_path.read_text(encoding="utf-8").splitlines()

        blocks: list[list[str]] = []
        current: list[str] = []
        for line in lines:
            if line.strip().startswith("|"):
                current.append(line)
            elif current:
                blocks.append(current)
                current = []
        if current:
            blocks.append(current)

        if not blocks:
            raise ValueError("spawn-matrix markdown table not found or malformed")

        selected_rows: list[list[str]] | None = None
        header: list[str] = []
        index: dict[str, int] = {}

        for block in blocks:
            rows = [[cell.strip() for cell in row.strip().strip("|").split("|")] for row in block]
            if len(rows) < 2:
                continue

            candidate_header = [h.lower() for h in rows[0]]
            candidate_index = {name: i for i, name in enumerate(candidate_header)}
            if all(column in candidate_index for column in self.REQUIRED_COLUMNS):
                selected_rows = rows
                header = candidate_header
                index = candidate_index
                break

        if selected_rows is None:
            raise ValueError(
                "spawn-matrix is missing required columns: " + ", ".join(self.REQUIRED_COLUMNS)
            )

        agents: list[dict[str, Any]] = []
        for row in selected_rows[2:]:  # skip header + markdown separator
            if len(row) < len(header):
                row = row + [""] * (len(header) - len(row))

            num_raw = row[index["#"]].strip()
            if not re.fullmatch(r"\d+", num_raw):
                continue

            number = int(num_raw)
            agents.append(
                {
                    "number": number,
                    "name": row[index["step"]].strip(),
                    "model": row[index["model"]].strip(),
                    "timeout_min": self._parse_timeout_minutes(row[index["timeout"]]),
                    "input_paths": self._split_input_paths(row[index["input paths"]]),
                    "output_path_expected": row[index["output path"]].strip(),
                    "task": row[index["task"]].strip(),
                    "acceptance_criteria": row[index["acceptance criteria"]].strip(),
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "output_path": None,
                    "r10a_status": None,
                    "r10a_path": None,
                    "attempts": 0,
                    "max_attempts": 3,
                }
            )

        agents.sort(key=lambda agent: agent["number"])
        if not agents:
            raise ValueError("spawn-matrix has no executable agent rows")
        return agents

    def init_state(self, force: bool = False) -> dict[str, Any]:
        if self.state_path.exists() and not force:
            raise FileExistsError(f"{self.state_path.name} already exists (use --force)")

        agents = self.parse_spawn_matrix()
        state = {
            "version": self._infer_version(self.accumulation_dir),
            "started_at": self.now_iso(),
            "current_step": 0,
            "pipeline_status": "initialized",
            "workerSessionKey": None,
            "r10_plugin": "r10_plugins.passthrough.PassthroughPlugin",
            "agents": agents,
        }
        self._save_json(self.state_path, state)
        return state

    def load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            raise FileNotFoundError(f"{self.state_path.name} not found (run --init first)")
        return self._load_json(self.state_path)

    def persist_state(self, state: dict[str, Any]) -> None:
        self._save_json(self.state_path, state)

    @staticmethod
    def _find_agent(state: dict[str, Any], agent_number: int) -> tuple[int, dict[str, Any]]:
        for index, agent in enumerate(state.get("agents", [])):
            if int(agent.get("number", -1)) == int(agent_number):
                return index, agent
        raise ValueError(f"agent {agent_number} not found in state")

    @staticmethod
    def _advance_current_step(state: dict[str, Any]) -> None:
        agents = state.get("agents", [])
        idx = int(state.get("current_step", 0))

        while idx < len(agents):
            agent = agents[idx]
            if agent.get("status") == "skipped":
                idx += 1
                continue
            if agent.get("status") == "done" and agent.get("r10a_status") is not None:
                idx += 1
                continue
            break

        state["current_step"] = idx
        if idx >= len(agents):
            state["pipeline_status"] = "completed"

    def next_step(self, state: dict[str, Any]) -> tuple[dict[str, Any], int]:
        if state.get("pipeline_status") == "completed":
            return {"status": "completed"}, EXIT_OK

        if state.get("pipeline_status") == "failed":
            return {"status": "failed", "reason": "pipeline marked as failed"}, EXIT_BLOCKED

        self._advance_current_step(state)
        if state.get("pipeline_status") == "completed":
            return {"status": "completed"}, EXIT_OK

        index = int(state.get("current_step", 0))
        agents = state.get("agents", [])
        if index >= len(agents):
            state["pipeline_status"] = "completed"
            return {"status": "completed"}, EXIT_OK

        agent = agents[index]

        if agent.get("status") == "done" and agent.get("r10a_status") is None:
            return {
                "status": "blocked_r10a",
                "reason": f"Agent {agent['number']} ({agent['name']}) completed but R10a not recorded.",
                "agent_number": agent["number"],
            }, EXIT_BLOCKED

        if agent.get("status") == "pending":
            agent["status"] = "running"
            if not agent.get("started_at"):
                agent["started_at"] = self.now_iso()

        state["pipeline_status"] = "running"
        payload = {
            "number": agent["number"],
            "name": agent["name"],
            "model": agent["model"],
            "timeout_min": agent["timeout_min"],
            "input_paths": agent.get("input_paths", []),
            "output_path": agent.get("output_path_expected"),
            "task": agent.get("task", ""),
        }
        return payload, EXIT_OK

    @staticmethod
    def summarize_r10a_status(r10a_path: str | Path) -> str:
        """Best-effort extraction of PASS/FAIL status from a validation JSON."""
        try:
            data = PipelineEngine._load_json(Path(r10a_path))
        except Exception:
            return "fail"

        if isinstance(data, dict):
            status = str(data.get("status", "")).strip().lower()
            if status in {"pass", "passed", "ok"}:
                return "pass"
            if status in {"fail", "failed", "error"}:
                return "fail"

            if "all_passed" in data:
                return "pass" if bool(data["all_passed"]) else "fail"

        as_text = json.dumps(data, ensure_ascii=False).lower()
        return "fail" if '"fail"' in as_text or '"failed"' in as_text else "pass"

    @staticmethod
    def build_dispatch_task(agent_spec: dict[str, Any]) -> str:
        input_paths = agent_spec.get("input_paths", [])
        input_lines = "\n".join([f"- {item}" for item in input_paths]) if input_paths else "- (none)"

        return "\n".join(
            [
                f"Agent {agent_spec.get('number')} — {agent_spec.get('name')}",
                "",
                "Task:",
                str(agent_spec.get("task", "")).strip(),
                "",
                "Input paths:",
                input_lines,
                "",
                "Output path:",
                str(agent_spec.get("output_path", "")).strip(),
            ]
        )

    @staticmethod
    def run_r10a_plugin(plugin_path: str, agent_output_path: str, reference_data_path: str, agent_number: int) -> dict[str, Any]:
        """Run a configured R10a plugin class.

        `plugin_path` format: `package.module.ClassName`.
        Accepted module roots include both `r10_plugins.*` and `scripts.r10_plugins.*`.
        """
        module_name, class_name = plugin_path.rsplit(".", 1)

        tried: list[str] = []
        module = None
        for candidate in [module_name, f"scripts.{module_name}"]:
            try:
                module = importlib.import_module(candidate)
                break
            except ModuleNotFoundError:
                tried.append(candidate)

        if module is None:
            raise ModuleNotFoundError(f"Unable to import plugin module. Tried: {tried}")

        cls = getattr(module, class_name)
        plugin = cls()
        return plugin.validate(
            agent_output_path=agent_output_path,
            reference_data_path=reference_data_path,
            agent_number=agent_number,
        )

    def record_completion(self, state: dict[str, Any], agent_number: int, status: str, output_path: str | None) -> dict[str, Any]:
        idx, agent = self._find_agent(state, agent_number)
        completion_status = status.strip().lower()
        if completion_status not in {"done", "failed"}:
            raise ValueError("completion status must be done or failed")

        if completion_status == "done":
            agent["status"] = "done"
            agent["completed_at"] = self.now_iso()
            agent["output_path"] = output_path
            self._advance_current_step(state)
            if state.get("pipeline_status") != "completed":
                state["pipeline_status"] = "running"
            return agent

        # failed
        agent["attempts"] = int(agent.get("attempts", 0)) + 1
        agent["completed_at"] = self.now_iso()
        agent["output_path"] = output_path

        if int(agent["attempts"]) >= int(agent.get("max_attempts", 3)):
            agent["status"] = "failed"
            state["pipeline_status"] = "failed"
        else:
            agent["status"] = "pending"
            agent["started_at"] = None
            agent["completed_at"] = None
            state["pipeline_status"] = "running"

        state["current_step"] = idx
        return agent


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _find_repo_doctor(accumulation_dir: Path) -> Path | None:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "repo_doctor.sh",
        accumulation_dir.parent / "repo_doctor.sh",
        accumulation_dir.parent / "scripts" / "repo_doctor.sh",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _run_repo_doctor_or_warn(accumulation_dir: Path) -> int:
    doctor_path = _find_repo_doctor(accumulation_dir)
    if doctor_path is None:
        print(
            "[WARN] repo_doctor.sh not found. Proceeding with --init for backward compatibility.",
            file=sys.stderr,
        )
        return EXIT_OK

    result = subprocess.run(["bash", str(doctor_path)], check=False)
    if result.returncode != 0:
        print(
            "[INIT BLOCKED] repo_doctor.sh failed. Run 'bash scripts/new_pipeline.sh <dir>' first, or fix missing artifacts manually.",
            file=sys.stderr,
        )
        return EXIT_BLOCKED

    return EXIT_OK


def main() -> int:
    parser = argparse.ArgumentParser(description="Generic multi-agent pipeline engine")
    parser.add_argument("--accumulation-dir", required=True, help="Path to accumulation directory")

    parser.add_argument("--init", action="store_true", help="Initialize pipeline-state.json")
    parser.add_argument("--dispatch", action="store_true", help="Return next synchronous dispatch payload")
    parser.add_argument("--record-completion", action="store_true", help="Record agent completion")
    parser.add_argument("--record-r10a", action="store_true", help="Record R10a result")
    parser.add_argument("--set-worker", metavar="KEY", help="Persist workerSessionKey in pipeline state")
    parser.add_argument("--get-worker", action="store_true", help="Return workerSessionKey from pipeline state")
    parser.add_argument("--status", action="store_true", help="Show full pipeline state JSON")

    parser.add_argument("--force", action="store_true", help="Overwrite state on --init")
    parser.add_argument("--agent-number", type=int, help="Agent number")
    parser.add_argument("--output-path", help="Output artifact path")
    parser.add_argument("--result", choices=["done", "failed"], help="Completion status for --record-completion")
    parser.add_argument("--r10a-path", help="Path to R10a validation JSON")

    args = parser.parse_args()
    engine = PipelineEngine(args.accumulation_dir)

    try:
        if args.init:
            gate_code = _run_repo_doctor_or_warn(engine.accumulation_dir)
            if gate_code != EXIT_OK:
                return gate_code

            state = engine.init_state(force=args.force)
            _print_json({"status": "initialized", "state_path": str(engine.state_path), "agents": len(state.get("agents", []))})
            return EXIT_OK

        if args.status:
            _print_json(engine.load_state())
            return EXIT_OK

        if args.dispatch:
            state = engine.load_state()
            spec, code = engine.next_step(state)
            engine.persist_state(state)
            if code != EXIT_OK:
                _print_json(spec)
                return code

            worker_session_key = state.get("workerSessionKey")
            if not worker_session_key:
                _print_json({"status": "error", "error": "bootstrap worker first"})
                return EXIT_BLOCKED

            task = PipelineEngine.build_dispatch_task(spec)
            _print_json(
                {
                    "status": "ready",
                    "workerSessionKey": worker_session_key,
                    "task": task,
                    "agent": spec,
                }
            )
            return EXIT_OK

        if args.record_completion:
            if args.agent_number is None or not args.result:
                raise ValueError("--record-completion requires --agent-number and --result done|failed")

            state = engine.load_state()
            agent = engine.record_completion(
                state=state,
                agent_number=args.agent_number,
                status=args.result,
                output_path=args.output_path,
            )
            engine.persist_state(state)
            _print_json({"status": "ok", "pipeline_status": state.get("pipeline_status"), "agent": agent})
            return EXIT_BLOCKED if state.get("pipeline_status") == "failed" else EXIT_OK

        if args.record_r10a:
            if args.agent_number is None or not args.r10a_path:
                raise ValueError("--record-r10a requires --agent-number and --r10a-path")

            state = engine.load_state()
            _, agent = PipelineEngine._find_agent(state, args.agent_number)
            summary_status = PipelineEngine.summarize_r10a_status(args.r10a_path)
            agent["r10a_status"] = summary_status
            agent["r10a_path"] = args.r10a_path
            engine.persist_state(state)
            _print_json({"status": "ok", "agent_number": args.agent_number, "r10a_status": summary_status})
            return EXIT_OK

        if args.set_worker:
            state = engine.load_state()
            state["workerSessionKey"] = args.set_worker
            engine.persist_state(state)
            _print_json({"status": "ok", "workerSessionKey": state.get("workerSessionKey")})
            return EXIT_OK

        if args.get_worker:
            state = engine.load_state()
            _print_json({"status": "ok", "workerSessionKey": state.get("workerSessionKey")})
            return EXIT_OK

        _print_json({"status": "error", "error": "No operation selected"})
        return EXIT_ERROR

    except Exception as exc:
        _print_json({"status": "error", "error": str(exc)})
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
