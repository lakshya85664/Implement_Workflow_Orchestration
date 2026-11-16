
"""
Topic 1 - Task 4
Integration Boundary and Observability.

Features:
- Injectable payment gateway
- Configurable dependency timeout
- Structured JSON events
- Metrics collection
- Status lookup
- Trace retrieval
- Failure recording
"""

import json
import time

from pathlib import Path
from typing import Any, Protocol

from metrics import WorkflowMetrics
from observability import WorkflowObserver


# ==================================================
# 1. Payment Gateway Contract
# ==================================================

class PaymentGateway(Protocol):

    def charge(
        self,
        order_id: str,
        amount: float,
        idempotency_key: str,
        timeout_seconds: float = 2.0,
    ) -> dict[str, Any]:
        ...


# ==================================================
# 2. Payment Adapter
# ==================================================

class PaymentAdapter:

    def __init__(
        self,
        gateway: PaymentGateway,
        observer: WorkflowObserver,
        metrics: WorkflowMetrics,
        timeout_seconds: float = 2.0,
    ):

        if timeout_seconds <= 0:

            raise ValueError(
                "Timeout must be positive"
            )

        self.gateway = gateway

        self.observer = observer

        self.metrics = metrics

        self.timeout_seconds = timeout_seconds

    # ------------------------------------------------
    # Payment processing
    # ------------------------------------------------

    def process_payment(
        self,
        order_id: str,
        amount: float,
        run_id: str,
    ) -> dict[str, Any]:

        started = time.perf_counter()

        self.observer.emit(
            run_id=run_id,
            event="payment.started",
            state="running",
            details={
                "order_id": order_id,
                "amount": amount,
                "timeout_seconds": self.timeout_seconds,
            },
        )

        try:

            response = self.gateway.charge(
                order_id=order_id,
                amount=amount,
                idempotency_key=f"payment:{order_id}",
                timeout_seconds=self.timeout_seconds,
            )

            # Validate dependency response.
            if not isinstance(response, dict):

                raise ValueError(
                    "Invalid payment response type"
                )

            if response.get("status") != "success":

                raise ValueError(
                    "Invalid payment response status"
                )

            latency_ms = (
                time.perf_counter() - started
            ) * 1000

            self.metrics.record_dependency(
                latency_ms=latency_ms,
                success=True,
            )

            self.metrics.record_run(
                success=True
            )

            self.observer.emit(
                run_id=run_id,
                event="payment.succeeded",
                state="completed",
                details={
                    "order_id": order_id,
                    "transaction_id": response.get(
                        "transaction_id"
                    ),
                    "latency_ms": round(
                        latency_ms,
                        3,
                    ),
                },
            )

            return response

        except Exception as exc:

            latency_ms = (
                time.perf_counter() - started
            ) * 1000

            self.metrics.record_dependency(
                latency_ms=latency_ms,
                success=False,
            )

            self.metrics.record_run(
                success=False
            )

            self.observer.emit(
                run_id=run_id,
                event="payment.failed",
                state="needs_review",
                details={
                    "order_id": order_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "latency_ms": round(
                        latency_ms,
                        3,
                    ),
                },
            )

            raise

    # ------------------------------------------------
    # Status lookup
    # ------------------------------------------------

    def status(self, run_id: str) -> dict:

        return self.observer.get_status(run_id)

    # ------------------------------------------------
    # Trace retrieval
    # ------------------------------------------------

    def trace(self, run_id: str) -> list[dict]:

        return self.observer.get_trace(run_id)


# ==================================================
# 3. Demonstration
# ==================================================

if __name__ == "__main__":

    from reliability import FakePaymentGateway

    observer = WorkflowObserver()

    metrics = WorkflowMetrics()

    gateway = FakePaymentGateway()

    adapter = PaymentAdapter(
        gateway=gateway,
        observer=observer,
        metrics=metrics,
        timeout_seconds=2.0,
    )

    response = adapter.process_payment(
        order_id="ORD-4001",
        amount=4500,
        run_id="RUN-4001",
    )

    metrics.record_queue_age(2.5)

    output = {

        "payment_response": response,

        "status": adapter.status("RUN-4001"),

        "trace": adapter.trace("RUN-4001"),

        "metrics": metrics.report(),
    }

    Path("outputs").mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        "outputs/task4_observability.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=4,
        )

    print("=" * 60)
    print("TASK 4 - INTEGRATION AND OBSERVABILITY")
    print("=" * 60)

    print(
        json.dumps(
            output,
            indent=4,
        )
    )

    print(
        "\nEvidence saved: "
        "outputs/task4_observability.json"
    )
