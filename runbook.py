
"""
Topic 1 - Task 5
Operator Runbook and Evidence Report

Documents operational actions for workflow states,
failure recovery, integration, timeout handling,
and assessment evidence.
"""

from pathlib import Path
import json


OPERATOR_ACTIONS = {
    "created": {
        "action": "Confirm that the order input is valid and ready for processing.",
        "next_step": "Start the workflow through the orchestration engine.",
    },
    "running": {
        "action": "Monitor task progress, payment processing, and dependency responses.",
        "next_step": "Continue execution or inspect the latest structured trace.",
    },
    "waiting": {
        "action": "Identify the pending dependency, approval, or external condition.",
        "next_step": "Resume only after the required condition is satisfied.",
    },
    "completed": {
        "action": "Verify payment authorization, packing, shipment, and completion records.",
        "next_step": "Confirm the final output and close the order.",
    },
    "needs_review": {
        "action": "Inspect error classification, retry history, timeout details, and payment side effects.",
        "next_step": "Authorize safe recovery or quarantine the order for manual review.",
    },
    "failed": {
        "action": "Inspect the terminal error, preserve traces, and identify incomplete tasks.",
        "next_step": "Escalate to the workflow operator before attempting recovery.",
    },
}


def get_operator_action(state: str) -> dict:
    """Return the recommended operator action for a workflow state."""

    if state not in OPERATOR_ACTIONS:
        raise ValueError(f"Unknown workflow state: {state}")

    return OPERATOR_ACTIONS[state]


def build_evidence_report():
    """Build the assessment evidence summary."""

    return {
        "topic": "Topic 1 - Workflow Orchestration",
        "project": "Order Fulfillment Workflow",
        "overall_status": "completed",
        "total_marks": 100,
        "total_tests": 34,
        "assessment_tasks": {
            "task1": {
                "name": "Workflow contract and state model",
                "marks": 15,
                "tests": 6,
                "status": "completed",
            },
            "task2": {
                "name": "Orchestration implementation",
                "marks": 25,
                "tests": 5,
                "status": "completed",
            },
            "task3": {
                "name": "Failure, retry and replay safety",
                "marks": 20,
                "tests": 9,
                "status": "completed",
            },
            "task4": {
                "name": "Integration and observability",
                "marks": 20,
                "tests": 7,
                "status": "completed",
            },
            "task5": {
                "name": "Operator runbook and evidence report",
                "marks": 20,
                "tests": 7,
                "status": "completed",
            },
        },
        "verified_behaviors": [
            "Order input validation",
            "Legal workflow state transitions",
            "Sequential order fulfillment orchestration",
            "Payment adapter integration with the orchestrator",
            "Transient dependency failure recovery",
            "Timeout and bounded retry handling",
            "Permanent failure classification",
            "Malformed response quarantine",
            "Duplicate payment protection through idempotency keys",
            "Cached result handling for duplicate workflow runs",
            "Structured event tracing",
            "Secret redaction in observability records",
            "Dependency metrics and latency measurements",
            "Operator actions for workflow states",
        ],
        "evidence_files": [
            "outputs/task2_happy_path.json",
            "outputs/task3_recovery.json",
            "outputs/task4_observability.json",
            "traces/task3_recovery_trace.json",
            "traces/task4_events.jsonl",
            "reports/OPERATOR_RUNBOOK.md",
            "reports/evidence_report.json",
        ],
        "known_limitations": [
            "The payment gateway is a local fake implementation.",
            "Retry backoff durations are calculated and recorded but are not actually slept.",
            "Idempotency and workflow run caches are in-memory and are not durable across process restarts.",
            "The fake gateway uses a cooperative deadline check; this does not cancel arbitrary blocking external network operations.",
            "A production payment adapter should enforce timeouts through its HTTP client or transport layer.",
            "A production deployment requires durable idempotency storage and persistent workflow state.",
            "Metrics are collected in process memory.",
            "The implementation does not include a distributed transaction coordinator.",
        ],
    }


def generate_runbook():
    """Generate the operator runbook Markdown file."""

    lines = [
        "# Operator Runbook",
        "",
        "## 1. Project overview",
        "",
        "This project implements an order fulfillment workflow.",
        "The orchestrator validates an order, processes payment,",
        "packs the order, and creates a shipment.",
        "",
        "Payment processing is integrated through a payment adapter.",
        "Structured events and metrics support operational monitoring.",
        "",
        "## 2. Normal operation",
        "",
        "1. Activate the Python virtual environment.",
        "2. Run the workflow demonstration.",
        "3. Inspect the saved JSON result.",
        "4. Verify the final workflow state.",
        "5. Confirm that payment, packing, and shipping tasks completed.",
        "",
        "## 3. Execution commands",
        "",
        "```cmd",
        "python workflow_orchestration.py",
        "python orchestrator.py",
        "python reliability.py",
        "python adapters.py",
        "python runbook.py",
        "python -m pytest -v",
        "```",
        "",
        "## 4. Failure handling",
        "",
        "- Timeout: retry within the configured attempt limit.",
        "- Transient dependency error: retry using bounded backoff.",
        "- Permanent dependency error: stop retries and request review.",
        "- Malformed response: quarantine the operation.",
        "- Retry exhaustion: request operator intervention.",
        "- Duplicate payment: reuse the same idempotency key.",
        "- Invalid order: stop before payment processing.",
        "",
        "## 5. Timeout and retry behavior",
        "",
        "- The fake payment gateway supports a configurable timeout.",
        "- A slow simulated operation checks its elapsed time against a deadline.",
        "- An operation exceeding the deadline raises a timeout error.",
        "- Retry attempts and calculated backoff durations are recorded.",
        "- The current retry implementation records backoff but does not sleep.",
        "- Production integrations must configure transport-level timeouts.",
        "",
        "## 6. Operator actions by state",
        "",
    ]

    for state, details in OPERATOR_ACTIONS.items():
        lines.extend([
            f"### {state.upper()}",
            f"- Action: {details['action']}",
            f"- Next step: {details['next_step']}",
            "",
        ])

    lines.extend([
        "## 7. Recovery procedure",
        "",
        "1. Identify the workflow run ID and order ID.",
        "2. Inspect the associated structured event traces.",
        "3. Determine whether the failure is retryable.",
        "4. Confirm the payment idempotency key.",
        "5. Check whether a payment side effect already occurred.",
        "6. Inspect the retry count and timeout information.",
        "7. Avoid creating a second payment for an already processed order.",
        "8. Resume only when the dependency and order state are safe.",
        "9. Save the recovery result and preserve the evidence.",
        "",
        "## 8. Evidence and monitoring",
        "",
        "- outputs/task2_happy_path.json: successful order fulfillment.",
        "- outputs/task3_recovery.json: retry, replay, and failure scenarios.",
        "- outputs/task4_observability.json: adapter response and metrics.",
        "- traces/task3_recovery_trace.json: recovery trace.",
        "- traces/task4_events.jsonl: structured integration events.",
        "- reports/evidence_report.json: assessment evidence summary.",
        "",
        "Monitor workflow state, dependency failures, retry attempts,",
        "latency measurements, and payment side effects.",
        "",
        "## 9. Known limitations",
        "",
        "- Local fake payment dependency only.",
        "- In-memory idempotency and workflow run caches.",
        "- No distributed transaction coordinator.",
        "- Cooperative timeout simulation rather than arbitrary I/O cancellation.",
        "- Retry backoff is recorded but not slept.",
        "- Metrics are process-local.",
        "",
        "## 10. Security",
        "",
        "- Never commit API keys or credentials.",
        "- Keep secrets in environment variables or managed secret stores.",
        "- Redact sensitive information from traces.",
        "- Use synthetic order and customer records.",
        "- Use durable, access-controlled storage for production payment records.",
    ])

    Path("reports").mkdir(exist_ok=True)

    runbook_path = Path("reports/OPERATOR_RUNBOOK.md")
    runbook_path.write_text("\n".join(lines), encoding="utf-8")

    return runbook_path.as_posix()


def save_evidence_report():
    """Save the assessment evidence report as JSON."""

    report = build_evidence_report()

    Path("reports").mkdir(exist_ok=True)

    report_path = Path("reports/evidence_report.json")

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    return report


if __name__ == "__main__":

    print("=" * 60)
    print("TASK 5 - OPERATOR RUNBOOK AND EVIDENCE REPORT")
    print("=" * 60)

    runbook_path = generate_runbook()
    report = save_evidence_report()

    print(f"Runbook generated: {runbook_path}")
    print("Evidence report generated: reports/evidence_report.json")

    print("\nOperator action for NEEDS_REVIEW:")

    print(json.dumps(
        get_operator_action("needs_review"),
        indent=4,
    ))

    print("\nEvidence summary:")

    print(json.dumps(report, indent=4))
