# Workflow Orchestration --- Order Fulfillment Workflow

## Project overview

This project implements a code-based workflow orchestration system for
an order fulfillment scenario. It validates an order, processes payment
through an adapter, packs the order, and creates a shipment. Explicit
workflow states and structured evidence make successful and unsuccessful
runs inspectable.

## Objectives

-   Define workflow contracts, state models, task dependencies, events,
    results, and legal transitions.
-   Coordinate order validation, payment, packing, and shipping.
-   Handle transient failures, timeouts, permanent failures, malformed
    responses, and retry exhaustion.
-   Prevent duplicate payment side effects with idempotency keys and
    replay-safe handling.
-   Integrate payment through an adapter boundary.
-   Capture structured events, redact sensitive values, and report
    operational metrics.
-   Provide an operator runbook and machine-readable evidence report.

## Architecture

1.  **Workflow contract and state model:** represents workflow input,
    tasks, events, results, traces, and run state.
2.  **Orchestrator:** validates the order and coordinates validation,
    payment, packing, and shipping.
3.  **Reliability layer:** classifies dependency errors, calculates
    bounded retry delays, applies idempotency, and supports replay-safe
    recovery.
4.  **Payment adapter:** isolates workflow logic from the payment
    gateway interface.
5.  **Observability and metrics:** records structured events, redacts
    sensitive fields, and measures dependency calls and latency.
6.  **Operator runbook:** documents state-specific actions, recovery
    steps, evidence locations, and known limitations.

## Workflow sequence

1.  Receive and validate the order.
2.  Transition the workflow into the running state.
3.  Process payment through the payment adapter.
4.  Pack the validated order.
5.  Create the shipment and tracking record.
6.  Mark the workflow completed and persist the result.

Retryable failures are retried within the configured attempt limit.
Permanent or malformed failures are not blindly retried. Retry
exhaustion or unsafe conditions require operator review.

## Reliability and replay safety

The project demonstrates timeout and transient failure recovery, bounded
retry calculations, permanent-failure handling, malformed-response
quarantine, duplicate-run result caching, and payment idempotency. The
replay demonstration confirms that repeating a payment operation with
the same idempotency key does not create a second payment side effect.

## Integration and observability

The orchestrator uses a payment adapter rather than depending directly
on gateway-specific implementation details. The adapter records start,
success, and failure events. Trace records include run identifiers,
event names, states, timestamps, and relevant details. Sensitive fields
are redacted. Metrics summarize run outcomes, dependency calls,
failures, attempts, latency, and queue age.

## Project structure

``` text
Implement_Workflow_Orchestration/
├── workflow_orchestration.py
├── orchestrator.py
├── reliability.py
├── adapters.py
├── observability.py
├── metrics.py
├── runbook.py
├── tests/
│   ├── test_workflow_contract.py
│   ├── test_orchestration.py
│   ├── test_failure_recovery.py
│   ├── test_adapters.py
│   └── test_operator_runbook.py
├── outputs/
├── traces/
├── reports/
├── requirements.txt
└── .gitignore
```

## Setup and execution

Run from Windows CMD in the project directory:

``` cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python orchestrator.py
python reliability.py
python adapters.py
python runbook.py
python -m pytest -v
```

If `.venv` already exists, activate it rather than recreating it.

## Verification results

  Assessment task                          Tests passed
  -------------------------------------- --------------
  Workflow contract and state model                 6/6
  Orchestration implementation                      5/5
  Failure, retry and replay safety                  9/9
  Integration and observability                     7/7
  Operator runbook and evidence report              7/7
  **Total**                                   **34/34**

The final full test run completed successfully. Demonstration scripts
generated the expected JSON outputs and trace files. The evidence report
records all five assessment tasks as completed.

## Evidence files

-   `outputs/task2_happy_path.json` --- successful order fulfillment
    result.
-   `outputs/task3_recovery.json` --- retry, replay, malformed-response,
    and retry-exhaustion scenarios.
-   `outputs/task4_observability.json` --- adapter response, trace, and
    metrics.
-   `traces/task3_recovery_trace.json` --- recovery trace.
-   `traces/task4_events.jsonl` --- structured integration events.
-   `reports/OPERATOR_RUNBOOK.md` --- operational procedures and
    recovery guidance.
-   `reports/evidence_report.json` --- assessment status and evidence
    inventory.

## Known limitations

-   The payment gateway is a local fake implementation, not a live
    payment provider.
-   Retry backoff durations are calculated and recorded but are not
    actually slept.
-   Idempotency and workflow run caches are in-memory and do not survive
    process restarts.
-   The fake gateway uses a cooperative deadline check; it cannot cancel
    arbitrary blocking external network operations. A production adapter
    must enforce timeouts at the HTTP client or transport layer.
-   Metrics are process-local.
-   The project does not implement a distributed transaction coordinator
    or durable workflow-state store.

## Reflection

Building this workflow orchestration project helped me understand how a
multi-step business process can be represented as explicit states,
tasks, dependencies, and transitions instead of a collection of loosely
connected function calls. I started by defining the workflow contract
and legal state transitions, which made expected behaviour clearer and
provided a foundation for testing. I then implemented the orchestrator
to coordinate order validation, payment, packing, and shipping in a
controlled sequence.

The reliability work demonstrated that handling an exception is not
enough for a production-style workflow. Different failures need
different responses. Transient errors and timeouts may be retried within
a limit, while permanent errors and malformed responses require
different handling. Idempotency was an important lesson: replaying an
operation must not accidentally repeat a payment side effect. The tests
helped verify that the same payment key protects against duplicate
charges.

Integrating the payment adapter clarified the value of separating
business workflow logic from an external dependency. Structured traces,
secret redaction, and metrics made the system easier to inspect.
Creating the operator runbook connected implementation details to
practical recovery actions.

The project is a local demonstration rather than a production payment
system. It uses a fake gateway, in-memory caches, and recorded rather
than delayed retry backoff. A production version would need durable
state and idempotency storage, transport-level timeout enforcement,
persistent observability, and stronger operational controls. Overall,
this activity strengthened my understanding of orchestration, dependency
boundaries, replay safety, failure recovery, and evidence-driven
testing.
