
"""
Topic 1 - Task 3 and Task 4
Failure, Retry, Replay Safety and Dependency Timeout.

Features:
- Error classification
- Bounded retries
- Exponential backoff calculation
- Timeout handling
- Malformed response handling
- Permanent failure handling
- Idempotent payment processing
- Duplicate run protection
- Recovery traces
- Cooperative dependency deadline enforcement
"""

import json
import time

from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable


# ==================================================
# 1. Error Classification
# ==================================================

class TransientDependencyError(Exception):
    """Temporary dependency failure."""


class PermanentDependencyError(Exception):
    """Non-recoverable dependency failure."""


class MalformedResponseError(Exception):
    """Dependency returned an invalid response."""


class DependencyTimeout(TimeoutError):
    """Dependency exceeded its allowed deadline."""


# ==================================================
# 2. Retry Policy
# ==================================================

@dataclass
class RetryPolicy:

    max_attempts: int = 3
    initial_backoff: float = 1.0
    max_backoff: float = 4.0

    def __post_init__(self):

        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if self.initial_backoff < 0:
            raise ValueError("initial_backoff cannot be negative")

        if self.max_backoff < 0:
            raise ValueError("max_backoff cannot be negative")

    def backoff_for(self, attempt: int) -> float:

        if attempt < 1:
            raise ValueError("Attempt must be at least 1")

        delay = self.initial_backoff * (2 ** (attempt - 1))

        return min(delay, self.max_backoff)


# ==================================================
# 3. Retry Result
# ==================================================

@dataclass
class RetryResult:

    success: bool
    attempts: int
    result: Any = None
    error: str | None = None
    error_type: str | None = None
    next_action: str = "none"

    retry_trace: list[dict[str, Any]] = field(
        default_factory=list
    )


# ==================================================
# 4. Bounded Retry Executor
# ==================================================

class RetryExecutor:

    RETRYABLE_ERRORS = (
        TransientDependencyError,
        DependencyTimeout,
    )

    def __init__(self, policy=None):

        self.policy = policy or RetryPolicy()

    def execute(self, operation: Callable[[], Any]) -> RetryResult:

        trace = []

        for attempt in range(
            1,
            self.policy.max_attempts + 1
        ):

            try:

                result = operation()

                if not isinstance(result, dict):
                    raise MalformedResponseError(
                        "Expected a dictionary response"
                    )

                if result.get("status") != "success":
                    raise MalformedResponseError(
                        "Missing or invalid success status"
                    )

                trace.append({
                    "attempt": attempt,
                    "outcome": "success",
                    "next_action": "continue",
                })

                return RetryResult(
                    success=True,
                    attempts=attempt,
                    result=result,
                    next_action="continue_workflow",
                    retry_trace=trace,
                )

            except self.RETRYABLE_ERRORS as exc:

                exhausted = (
                    attempt == self.policy.max_attempts
                )

                delay = (
                    None if exhausted
                    else self.policy.backoff_for(attempt)
                )

                trace.append({
                    "attempt": attempt,
                    "outcome": "retryable_failure",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "backoff_seconds": delay,
                    "next_action": (
                        "operator_review"
                        if exhausted
                        else "retry"
                    ),
                })

                if exhausted:

                    return RetryResult(
                        success=False,
                        attempts=attempt,
                        error=str(exc),
                        error_type=type(exc).__name__,
                        next_action="operator_review",
                        retry_trace=trace,
                    )

            except (
                PermanentDependencyError,
                MalformedResponseError,
            ) as exc:

                trace.append({
                    "attempt": attempt,
                    "outcome": "permanent_failure",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "next_action": "quarantine",
                })

                return RetryResult(
                    success=False,
                    attempts=attempt,
                    error=str(exc),
                    error_type=type(exc).__name__,
                    next_action="quarantine_and_review",
                    retry_trace=trace,
                )

        raise RuntimeError("Unexpected retry executor exit")


# ==================================================
# 5. Fake Payment Gateway
# ==================================================

class FakePaymentGateway:
    """
    Local payment dependency.

    Supports:
    - Timeout simulation
    - Slow dependency simulation
    - Transient failure
    - Permanent failure
    - Malformed response
    - Idempotency protection
    """

    def __init__(self, failure_plan=None):

        self.failure_plan = list(failure_plan or [])

        self.processed_payments = {}

        self.call_count = 0
        self.side_effect_count = 0

    def charge(
        self,
        order_id: str,
        amount: float,
        idempotency_key: str,
        timeout_seconds: float = 2.0,
    ) -> dict[str, Any]:

        if timeout_seconds <= 0:
            raise ValueError(
                "Timeout must be positive"
            )

        started = time.monotonic()

        deadline = started + timeout_seconds

        self.call_count += 1

        # Replay protection.
        if idempotency_key in self.processed_payments:
            return self.processed_payments[idempotency_key]

        if amount <= 0:
            raise PermanentDependencyError(
                "Payment amount must be positive"
            )

        # Simulate dependency failures.
        if self.failure_plan:

            failure = self.failure_plan.pop(0)

            if failure == "timeout":

                raise DependencyTimeout(
                    "Payment gateway timed out"
                )

            if failure == "slow":

                # Simulate a slow dependency.
                time.sleep(timeout_seconds + 0.02)

                if time.monotonic() > deadline:

                    raise DependencyTimeout(
                        "Payment operation exceeded its deadline"
                    )

            if failure == "transient":

                raise TransientDependencyError(
                    "Temporary payment gateway failure"
                )

            if failure == "permanent":

                raise PermanentDependencyError(
                    "Payment authorization permanently declined"
                )

            if failure == "malformed":

                return {
                    "unexpected": "invalid response"
                }

        # Final deadline verification before side effect.
        if time.monotonic() > deadline:

            raise DependencyTimeout(
                "Payment deadline expired before processing"
            )

        # Protected payment side effect.
        self.side_effect_count += 1

        response = {
            "status": "success",
            "order_id": order_id,
            "amount": amount,
            "transaction_id": f"TXN-{order_id}",
        }

        self.processed_payments[idempotency_key] = response

        return response


# ==================================================
# 6. Payment Recovery Service
# ==================================================

class PaymentRecoveryService:

    def __init__(
        self,
        gateway: FakePaymentGateway,
        retry_executor=None,
    ):

        self.gateway = gateway

        self.retry_executor = (
            retry_executor or RetryExecutor()
        )

        self.run_cache = {}

    def process(
        self,
        order_id: str,
        amount: float,
        run_id: str,
    ) -> RetryResult:

        # Duplicate run protection.
        if run_id in self.run_cache:

            cached = self.run_cache[run_id]

            return RetryResult(
                success=cached.success,
                attempts=cached.attempts,
                result=cached.result,
                error=cached.error,
                error_type=cached.error_type,
                next_action="return_cached_result",
                retry_trace=cached.retry_trace.copy(),
            )

        idempotency_key = f"payment:{order_id}"

        result = self.retry_executor.execute(
            lambda: self.gateway.charge(
                order_id=order_id,
                amount=amount,
                idempotency_key=idempotency_key,
            )
        )

        # Cache successful results and terminal failures.
        # Retry exhaustion remains eligible for recovery.
        if (
            result.success
            or result.next_action == "quarantine_and_review"
        ):

            self.run_cache[run_id] = result

        return result


# ==================================================
# 7. Task 3 Demonstration
# ==================================================

def run_task3_demo():

    output_dir = Path("outputs")
    trace_dir = Path("traces")

    output_dir.mkdir(exist_ok=True)
    trace_dir.mkdir(exist_ok=True)

    # Scenario A: Timeout, transient failure, success.
    gateway = FakePaymentGateway(
        failure_plan=["timeout", "transient"]
    )

    service = PaymentRecoveryService(
        gateway=gateway,
        retry_executor=RetryExecutor(
            RetryPolicy(max_attempts=3)
        ),
    )

    recovery = service.process(
        order_id="ORD-3001",
        amount=3500,
        run_id="RUN-3001",
    )

    # Scenario B: Replay.
    replay = service.process(
        order_id="ORD-3001",
        amount=3500,
        run_id="RUN-3001",
    )

    # Scenario C: Malformed response.
    malformed_service = PaymentRecoveryService(
        FakePaymentGateway(
            failure_plan=["malformed"]
        )
    )

    malformed = malformed_service.process(
        order_id="ORD-3002",
        amount=2000,
        run_id="RUN-3002",
    )

    # Scenario D: Retry exhaustion.
    failed_service = PaymentRecoveryService(
        FakePaymentGateway(
            failure_plan=[
                "timeout",
                "timeout",
                "timeout",
            ]
        )
    )

    exhausted = failed_service.process(
        order_id="ORD-3003",
        amount=1500,
        run_id="RUN-3003",
    )

    output = {

        "recovery": {
            "success": recovery.success,
            "attempts": recovery.attempts,
            "result": recovery.result,
            "next_action": recovery.next_action,
            "trace": recovery.retry_trace,
        },

        "replay": {
            "success": replay.success,
            "next_action": replay.next_action,
            "payment_side_effect_count": gateway.side_effect_count,
        },

        "malformed_response": {
            "success": malformed.success,
            "error_type": malformed.error_type,
            "next_action": malformed.next_action,
        },

        "retry_exhaustion": {
            "success": exhausted.success,
            "attempts": exhausted.attempts,
            "next_action": exhausted.next_action,
            "trace": exhausted.retry_trace,
        },
    }

    with open(
        output_dir / "task3_recovery.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(output, file, indent=4)

    with open(
        trace_dir / "task3_recovery_trace.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            recovery.retry_trace,
            file,
            indent=4,
        )

    return output


if __name__ == "__main__":

    print("=" * 60)
    print("TASK 3 - FAILURE, RETRY AND REPLAY SAFETY")
    print("=" * 60)

    print(
        json.dumps(
            run_task3_demo(),
            indent=4,
        )
    )
