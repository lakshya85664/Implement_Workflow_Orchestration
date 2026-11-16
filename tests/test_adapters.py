
"""
Task 4 - Integration Adapter Tests

Covers:
- Payment success
- Structured traces
- Dependency failure
- Secret redaction
- Metrics
- Actual cooperative timeout enforcement
- Invalid timeout configuration
"""

import pytest

from adapters import PaymentAdapter

from metrics import WorkflowMetrics

from observability import WorkflowObserver

from reliability import FakePaymentGateway


# ==================================================
# Test Fixtures
# ==================================================

def create_adapter(
    tmp_path,
    failure_plan=None,
    timeout_seconds=2.0,
):

    trace_file = tmp_path / "events.jsonl"

    observer = WorkflowObserver(
        str(trace_file)
    )

    metrics = WorkflowMetrics()

    gateway = FakePaymentGateway(
        failure_plan=failure_plan
    )

    adapter = PaymentAdapter(
        gateway=gateway,
        observer=observer,
        metrics=metrics,
        timeout_seconds=timeout_seconds,
    )

    return adapter, observer, metrics, gateway


# ==================================================
# 1. Payment Success
# ==================================================

def test_payment_adapter_success(tmp_path):

    adapter, observer, metrics, gateway = create_adapter(
        tmp_path
    )

    result = adapter.process_payment(
        "ORD-401",
        2000,
        "RUN-401",
    )

    assert result["status"] == "success"

    assert (
        adapter.status("RUN-401")["state"]
        == "completed"
    )

    assert metrics.runs_succeeded == 1

    assert metrics.dependency_calls == 1


# ==================================================
# 2. Structured Trace
# ==================================================

def test_structured_trace_is_generated(tmp_path):

    adapter, observer, metrics, gateway = create_adapter(
        tmp_path
    )

    adapter.process_payment(
        "ORD-402",
        3000,
        "RUN-402",
    )

    trace = adapter.trace("RUN-402")

    assert len(trace) == 2

    assert trace[0]["event"] == "payment.started"

    assert trace[1]["event"] == "payment.succeeded"

    for event in trace:

        assert event["trace_id"]

        assert event["timestamp"]

        assert event["run_id"] == "RUN-402"


# ==================================================
# 3. Dependency Failure
# ==================================================

def test_dependency_failure_is_observable(tmp_path):

    adapter, observer, metrics, gateway = create_adapter(
        tmp_path,
        failure_plan=["permanent"],
    )

    with pytest.raises(Exception):

        adapter.process_payment(
            "ORD-403",
            1500,
            "RUN-403",
        )

    assert metrics.runs_failed == 1

    assert metrics.dependency_failures == 1

    trace = adapter.trace("RUN-403")

    assert trace[-1]["event"] == "payment.failed"

    assert trace[-1]["state"] == "needs_review"


# ==================================================
# 4. Secret Redaction
# ==================================================

def test_secrets_are_redacted(tmp_path):

    adapter, observer, metrics, gateway = create_adapter(
        tmp_path
    )

    observer.emit(
        run_id="RUN-404",
        event="security.test",
        state="running",
        details={
            "api_key": "SECRET-123",
            "password": "PASSWORD-123",
            "order_id": "ORD-404",
        },
    )

    trace = adapter.trace("RUN-404")

    details = trace[0]["details"]

    assert details["api_key"] == "[REDACTED]"

    assert details["password"] == "[REDACTED]"

    assert details["order_id"] == "ORD-404"

    raw_trace = (
        tmp_path / "events.jsonl"
    ).read_text(
        encoding="utf-8"
    )

    assert "SECRET-123" not in raw_trace

    assert "PASSWORD-123" not in raw_trace


# ==================================================
# 5. Metrics
# ==================================================

def test_metrics_report(tmp_path):

    adapter, observer, metrics, gateway = create_adapter(
        tmp_path
    )

    adapter.process_payment(
        "ORD-405",
        2500,
        "RUN-405",
    )

    metrics.record_queue_age(5)

    report = metrics.report()

    assert report["runs"]["started"] == 1

    assert report["runs"]["succeeded"] == 1

    assert report["runs"]["success_rate_percent"] == 100

    assert report["dependencies"]["calls"] == 1

    assert report["latency"]["total_ms"] >= 0

    assert report["queue"]["total_age_seconds"] == 5


# ==================================================
# 6. Actual Cooperative Timeout Enforcement
# ==================================================

def test_slow_dependency_times_out_without_payment_side_effect(
    tmp_path,
):

    adapter, observer, metrics, gateway = create_adapter(
        tmp_path,
        failure_plan=["slow"],
        timeout_seconds=0.01,
    )

    with pytest.raises(
        Exception,
        match="deadline",
    ):

        adapter.process_payment(
            "ORD-406",
            2500,
            "RUN-406",
        )

    # No payment side effect should occur.
    assert gateway.side_effect_count == 0

    # Failure must be recorded.
    assert metrics.dependency_failures == 1

    trace = adapter.trace("RUN-406")

    assert trace[-1]["event"] == "payment.failed"

    assert (
        trace[-1]["details"]["error_type"]
        == "DependencyTimeout"
    )


# ==================================================
# 7. Invalid Timeout Configuration
# ==================================================

def test_invalid_adapter_timeout_rejected(tmp_path):

    with pytest.raises(
        ValueError,
        match="Timeout must be positive",
    ):

        PaymentAdapter(
            gateway=FakePaymentGateway(),

            observer=WorkflowObserver(
                str(tmp_path / "invalid.jsonl")
            ),

            metrics=WorkflowMetrics(),

            timeout_seconds=0,
        )
