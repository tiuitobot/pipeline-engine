#!/usr/bin/env python3
"""Run an R10a mechanical validation plugin and write JSON output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipeline_engine import PipelineEngine


def main() -> int:
    parser = argparse.ArgumentParser(description="Run R10a mechanical validation plugin")
    parser.add_argument("--plugin", required=True, help="Plugin class path (e.g. r10_plugins.passthrough.PassthroughPlugin)")
    parser.add_argument("--agent-output", required=True, help="Agent output file path")
    parser.add_argument("--reference-data", required=True, help="Reference data path for plugin")
    parser.add_argument("--agent-number", required=True, type=int, help="Agent number")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    result = PipelineEngine.run_r10a_plugin(
        plugin_path=args.plugin,
        agent_output_path=args.agent_output,
        reference_data_path=args.reference_data,
        agent_number=args.agent_number,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if str(result.get("status", "")).upper() == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
