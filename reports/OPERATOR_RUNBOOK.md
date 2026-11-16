# Operator Runbook

## 1. Project overview

This project implements an order fulfillment workflow.
The orchestrator validates an order, processes payment,
packs the order, and creates a shipment.

Payment processing is integrated through a payment adapter.
Structured events and metrics support operational monitoring.

## 2. Normal operation

1. Activate the Python virtual environment.
2. Run the workflow demonstration.
3. Inspect the saved JSON result.
4. Verify the final workflow state.
5. Confirm that payment, packing, and shipping tasks completed.

## 3. Execution commands

```cmd
python workflow_orchestration.py
python orchestrator.py
python reliability.py
python adapters.py
python runbook.py
python -m pytest -v
```

## 4. Failure handling

- Timeout: retry within the configured attempt limit.
- Transient dependency error: retry using bounded backoff.
- Permanent dependency error: stop retries and request review.
- Malformed response: quarantine the operation.
- Retry exhaustion: request operator intervention.
- Duplicate payment: reuse the same idempotency key.
- Invalid order: stop before payment processing.

## 5. Timeout and retry behavior

- The fake payment gateway supports a configurable timeout.
- A slow simulated operation checks its elapsed time against a deadline.
- An operation exceeding the deadline raises a timeout error.
- Retry attempts and calculated backoff durations are recorded.
- The current retry implementation records backoff but does not sleep.
- Production integrations must configure transport-level timeouts.

## 6. Operator actions by state

### CREATED
- Action: Confirm that the order input is valid and ready for processing.
- Next step: Start the workflow through the orchestration engine.

### RUNNING
- Action: Monitor task progress, payment processing, and dependency responses.
- Next step: Continue execution or inspect the latest structured trace.

### WAITING
- Action: Identify the pending dependency, approval, or external condition.
- Next step: Resume only after the required condition is satisfied.

### COMPLETED
- Action: Verify payment authorization, packing, shipment, and completion records.
- Next step: Confirm the final output and close the order.

### NEEDS_REVIEW
- Action: Inspect error classification, retry history, timeout details, and payment side effects.
- Next step: Authorize safe recovery or quarantine the order for manual review.

### FAILED
- Action: Inspect the terminal error, preserve traces, and identify incomplete tasks.
- Next step: Escalate to the workflow operator before attempting recovery.

## 7. Recovery procedure

1. Identify the workflow run ID and order ID.
2. Inspect the associated structured event traces.
3. Determine whether the failure is retryable.
4. Confirm the payment idempotency key.
5. Check whether a payment side effect already occurred.
6. Inspect the retry count and timeout information.
7. Avoid creating a second payment for an already processed order.
8. Resume only when the dependency and order state are safe.
9. Save the recovery result and preserve the evidence.

## 8. Evidence and monitoring

- outputs/task2_happy_path.json: successful order fulfillment.
- outputs/task3_recovery.json: retry, replay, and failure scenarios.
- outputs/task4_observability.json: adapter response and metrics.
- traces/task3_recovery_trace.json: recovery trace.
- traces/task4_events.jsonl: structured integration events.
- reports/evidence_report.json: assessment evidence summary.

Monitor workflow state, dependency failures, retry attempts,
latency measurements, and payment side effects.

## 9. Known limitations

- Local fake payment dependency only.
- In-memory idempotency and workflow run caches.
- No distributed transaction coordinator.
- Cooperative timeout simulation rather than arbitrary I/O cancellation.
- Retry backoff is recorded but not slept.
- Metrics are process-local.

## 10. Security

- Never commit API keys or credentials.
- Keep secrets in environment variables or managed secret stores.
- Redact sensitive information from traces.
- Use synthetic order and customer records.
- Use durable, access-controlled storage for production payment records.