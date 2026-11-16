
"""
Task 4 - Workflow Observability

Provides structured JSON traces, status lookup,
trace retrieval, and secret redaction.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


SENSITIVE_KEYS = {
    "password",
    "secret",
    "api_key",
    "token",
    "authorization",
    "credential",
}


def redact_secrets(data: Any) -> Any:

    if isinstance(data, dict):

        return {
            key: (
                "[REDACTED]"
                if key.lower() in SENSITIVE_KEYS
                else redact_secrets(value)
            )
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [redact_secrets(item) for item in data]

    return data


class WorkflowObserver:

    def __init__(self, trace_file="traces/task4_events.jsonl"):

        self.trace_file = Path(trace_file)
        self.trace_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.run_status = {}

    def emit(
        self,
        run_id: str,
        event: str,
        state: str,
        details: dict | None = None,
    ) -> dict:

        record = {
            "trace_id": str(uuid4()),
            "run_id": run_id,
            "event": event,
            "state": state,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "details": redact_secrets(details or {}),
        }

        with self.trace_file.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(record) + "\n"
            )

        self.run_status[run_id] = {
            "state": state,
            "last_event": event,
        }

        return record

    def get_status(self, run_id: str) -> dict:

        return self.run_status.get(
            run_id,
            {
                "state": "unknown",
                "last_event": None,
            },
        )

    def get_trace(self, run_id: str) -> list[dict]:

        if not self.trace_file.exists():
            return []

        matching_events = []

        with self.trace_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                record = json.loads(line)

                if record["run_id"] == run_id:
                    matching_events.append(record)

        return matching_events
