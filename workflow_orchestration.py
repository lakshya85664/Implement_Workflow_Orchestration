
"""
Topic 1: Implement Workflow Orchestration in Code
Task 1: Workflow Contract and State Model

Defines typed workflow models, legal states,
transition rules, and a runnable demonstration.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


# --------------------------------------------------
# 1. Workflow States
# --------------------------------------------------

class WorkflowState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


# --------------------------------------------------
# 2. Workflow Input Model
# --------------------------------------------------

@dataclass
class WorkflowInput:
    order_id: str
    customer_id: str
    amount: float
    items: list[str]
    requires_approval: bool = False

    def validate(self) -> None:
        if not self.order_id:
            raise ValueError("Order ID is required")

        if not self.customer_id:
            raise ValueError("Customer ID is required")

        if self.amount <= 0:
            raise ValueError("Order amount must be positive")

        if not self.items:
            raise ValueError("Order must contain at least one item")


# --------------------------------------------------
# 3. Task Model
# --------------------------------------------------

@dataclass
class WorkflowTask:
    task_id: str
    name: str
    status: str = "pending"
    attempts: int = 0
    dependencies: list[str] = field(default_factory=list)
    result: Any = None


# --------------------------------------------------
# 4. Event Model
# --------------------------------------------------

@dataclass
class WorkflowEvent:
    run_id: str
    event: str
    state: str
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------
# 5. Result Model
# --------------------------------------------------

@dataclass
class WorkflowResult:
    run_id: str
    status: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


# --------------------------------------------------
# 6. Trace Model
# --------------------------------------------------

@dataclass
class WorkflowTrace:
    run_id: str
    trace_id: str
    operation: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------
# 7. Workflow Run Model
# --------------------------------------------------

@dataclass
class WorkflowRun:
    run_id: str
    business_key: str
    state: WorkflowState = WorkflowState.CREATED
    attempts: int = 0
    context: dict[str, Any] = field(default_factory=dict)
    events: list[WorkflowEvent] = field(default_factory=list)
    tasks: list[WorkflowTask] = field(default_factory=list)
    traces: list[WorkflowTrace] = field(default_factory=list)

    def record(self, event: str, **details: Any) -> None:
        self.events.append(
            WorkflowEvent(
                run_id=self.run_id,
                event=event,
                state=self.state.value,
                timestamp=datetime.now(timezone.utc).isoformat(),
                details=details,
            )
        )


# --------------------------------------------------
# 8. Legal State Transitions
# --------------------------------------------------

LEGAL_TRANSITIONS = {
    (WorkflowState.CREATED, "start"): WorkflowState.RUNNING,

    (WorkflowState.RUNNING, "complete"): WorkflowState.COMPLETED,
    (WorkflowState.RUNNING, "pause"): WorkflowState.WAITING,
    (WorkflowState.RUNNING, "fail"): WorkflowState.NEEDS_REVIEW,

    (WorkflowState.WAITING, "resume"): WorkflowState.RUNNING,

    (WorkflowState.NEEDS_REVIEW, "resume"): WorkflowState.RUNNING,
    (WorkflowState.NEEDS_REVIEW, "fail"): WorkflowState.FAILED,
}


# --------------------------------------------------
# 9. Transition Function
# --------------------------------------------------

def transition(
    run: WorkflowRun,
    event: str,
) -> WorkflowRun:

    next_state = LEGAL_TRANSITIONS.get((run.state, event))

    if next_state is None:
        raise ValueError(
            f"Illegal transition: {run.state.value} + {event}"
        )

    previous_state = run.state
    run.state = next_state

    run.record(
        event=event,
        previous_state=previous_state.value,
        next_state=next_state.value,
    )

    return run


# --------------------------------------------------
# 10. Topic 1 Demonstration
# --------------------------------------------------

def run_topic_fixture() -> dict[str, Any]:

    order = WorkflowInput(
        order_id="ORD-1001",
        customer_id="CUST-101",
        amount=2499.00,
        items=["Laptop Bag", "Wireless Mouse"],
    )

    order.validate()

    run = WorkflowRun(
        run_id="RUN-001",
        business_key=order.order_id,
        context={
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "amount": order.amount,
            "items": order.items,
        },
    )

    run.record("workflow.created", order_id=order.order_id)

    transition(run, "start")
    transition(run, "complete")

    result = WorkflowResult(
        run_id=run.run_id,
        status=run.state.value,
        success=True,
        output={
            "order_id": order.order_id,
            "message": "Workflow completed successfully",
        },
    )

    return {
        "status": result.status,
        "run_id": run.run_id,
        "business_key": run.business_key,
        "events": [
            event.event for event in run.events
        ],
        "result": result.output,
    }


# --------------------------------------------------
# 11. Main Execution
# --------------------------------------------------

if __name__ == "__main__":
    import json

    output = run_topic_fixture()

    print("=" * 60)
    print("TOPIC 1 - WORKFLOW ORCHESTRATION")
    print("=" * 60)

    print(json.dumps(output, indent=4))
