
import pytest

from reliability import (
    RetryPolicy,
    RetryExecutor,
    FakePaymentGateway,
    PaymentRecoveryService,
    DependencyTimeout,
    PermanentDependencyError,
    MalformedResponseError,
)


def test_timeout_then_success():

    gateway = FakePaymentGateway(
        failure_plan=["timeout"]
    )

    executor = RetryExecutor(
        RetryPolicy(max_attempts=3)
    )

    result = executor.execute(
        lambda: gateway.charge(
            "ORD-001", 1000, "payment:ORD-001"
        )
    )

    assert result.success is True
    assert result.attempts == 2
    assert result.retry_trace[0]["outcome"] == "retryable_failure"


def test_transient_failure_then_success():

    gateway = FakePaymentGateway(
        failure_plan=["transient"]
    )

    service = PaymentRecoveryService(gateway)

    result = service.process(
        "ORD-002", 2000, "RUN-002"
    )

    assert result.success is True
    assert result.attempts == 2


def test_retry_exhaustion():

    gateway = FakePaymentGateway(
        failure_plan=["timeout", "timeout", "timeout"]
    )

    service = PaymentRecoveryService(gateway)

    result = service.process(
        "ORD-003", 1500, "RUN-003"
    )

    assert result.success is False
    assert result.attempts == 3
    assert result.next_action == "operator_review"


def test_permanent_failure_is_not_retried():

    gateway = FakePaymentGateway(
        failure_plan=["permanent"]
    )

    executor = RetryExecutor()

    result = executor.execute(
        lambda: gateway.charge(
            "ORD-004", 1200, "payment:ORD-004"
        )
    )

    assert result.success is False
    assert result.attempts == 1
    assert result.error_type == "PermanentDependencyError"
    assert result.next_action == "quarantine_and_review"


def test_malformed_response_is_quarantined():

    gateway = FakePaymentGateway(
        failure_plan=["malformed"]
    )

    service = PaymentRecoveryService(gateway)

    result = service.process(
        "ORD-005", 1000, "RUN-005"
    )

    assert result.success is False
    assert result.error_type == "MalformedResponseError"
    assert result.attempts == 1


def test_duplicate_run_returns_cached_result():

    gateway = FakePaymentGateway()

    service = PaymentRecoveryService(gateway)

    first = service.process(
        "ORD-006", 2500, "RUN-006"
    )

    second = service.process(
        "ORD-006", 2500, "RUN-006"
    )

    assert first.success is True
    assert second.success is True
    assert second.next_action == "return_cached_result"
    assert gateway.side_effect_count == 1


def test_same_payment_key_prevents_duplicate_charge():

    gateway = FakePaymentGateway()

    service = PaymentRecoveryService(gateway)

    first = service.process(
        "ORD-007", 3000, "RUN-007-A"
    )

    second = service.process(
        "ORD-007", 3000, "RUN-007-B"
    )

    assert first.success is True
    assert second.success is True

    # Two requests, but only one actual payment effect.
    assert gateway.call_count == 2
    assert gateway.side_effect_count == 1


def test_backoff_is_bounded():

    policy = RetryPolicy(
        max_attempts=5,
        initial_backoff=1,
        max_backoff=4,
    )

    assert policy.backoff_for(1) == 1
    assert policy.backoff_for(2) == 2
    assert policy.backoff_for(3) == 4
    assert policy.backoff_for(4) == 4
    assert policy.backoff_for(5) == 4


def test_invalid_payment_amount():

    gateway = FakePaymentGateway()

    service = PaymentRecoveryService(gateway)

    result = service.process(
        "ORD-008", -100, "RUN-008"
    )

    assert result.success is False
    assert result.error_type == "PermanentDependencyError"
    assert gateway.side_effect_count == 0
