"""No-op R10a plugin for pipelines without mechanical validation needs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .base_plugin import R10Plugin


class PassthroughPlugin(R10Plugin):
    def validate(
        self,
        agent_output_path: str,
        reference_data_path: str,
        agent_number: int,
    ) -> dict[str, Any]:
        return {
            "agent": agent_number,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "PASS",
            "checks": [
                {
                    "id": "PASS-001",
                    "name": "passthrough",
                    "status": "pass",
                    "detail": "No mechanical validation configured for this pipeline.",
                }
            ],
            "errors": [],
            "summary": "1/1 checks passed",
            "metadata": {
                "agent_output_path": agent_output_path,
                "reference_data_path": reference_data_path,
            },
        }
