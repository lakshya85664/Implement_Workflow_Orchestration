
"""
Task 4 - Workflow Metrics

Tracks execution counts, outcomes, attempts,
latency, and queue age.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowMetrics:

    runs_started: int = 0
    runs_succeeded: int = 0
    runs_failed: int = 0

    dependency_calls: int = 0
    dependency_failures: int = 0

    total_attempts: int = 0
    total_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    total_queue_age_seconds: float = 0.0
    measurements: list[dict[str, Any]] = field(
        default_factory=list
    )

    def record_run(self, success: bool) -> None:

        self.runs_started += 1

        if success:
            self.runs_succeeded += 1
        else:
            self.runs_failed += 1

    def record_dependency(
        self,
        latency_ms: float,
        success: bool,
        attempts: int = 1,
    ) -> None:

        self.dependency_calls += 1
        self.total_attempts += attempts

        self.total_latency_ms += latency_ms

        self.max_latency_ms = max(
            self.max_latency_ms,
            latency_ms,
        )

        if not success:
            self.dependency_failures += 1

        self.measurements.append({
            "latency_ms": round(latency_ms, 3),
            "success": success,
            "attempts": attempts,
        })

    def record_queue_age(self, age_seconds: float) -> None:

        self.total_queue_age_seconds += max(
            0.0, age_seconds
        )

    def report(self) -> dict[str, Any]:

        total_runs = self.runs_started

        return {
            "runs": {
                "started": total_runs,
                "succeeded": self.runs_succeeded,
                "failed": self.runs_failed,
                "success_rate_percent": (
                    round(
                        self.runs_succeeded / total_runs * 100,
                        2,
                    )
                    if total_runs else 0
                ),
            },
            "dependencies": {
                "calls": self.dependency_calls,
                "failures": self.dependency_failures,
                "total_attempts": self.total_attempts,
                "failure_rate_percent": (
                    round(
                        self.dependency_failures
                        / self.dependency_calls * 100,
                        2,
                    )
                    if self.dependency_calls else 0
                ),
            },
            "latency": {
                "total_ms": round(self.total_latency_ms, 3),
                "max_ms": round(self.max_latency_ms, 3),
                "average_ms": (
                    round(
                        self.total_latency_ms
                        / self.dependency_calls,
                        3,
                    )
                    if self.dependency_calls else 0
                ),
            },
            "queue": {
                "total_age_seconds": round(
                    self.total_queue_age_seconds, 3
                ),
            },
        }
