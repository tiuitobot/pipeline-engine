"""Base interface for R10a mechanical validation plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class R10Plugin(ABC):
    """Abstract plugin API for mechanical validations."""

    @abstractmethod
    def validate(
        self,
        agent_output_path: str,
        reference_data_path: str,
        agent_number: int,
    ) -> dict[str, Any]:
        """Validate an agent output file against reference data.

        Returns a JSON-serializable dictionary with at least:
        - status: PASS|FAIL
        - checks: list
        - errors: list
        """
        raise NotImplementedError
