
import pytest

from workflow_orchestration import (
    WorkflowInput,
    WorkflowRun,
    WorkflowState,
    transition,
    run_topic_fixture,
)


def create_run():
    return WorkflowRun(
        run_id="TEST-RUN-001",
        business_key="ORDER-001",
    )


def test_valid_transition_created_to_running():
    run = create_run()

    transition(run, "start")

    assert run.state == WorkflowState.RUNNING
    assert len(run.events) == 1


def test_invalid_transition_created_to_completed():
    run = create_run()

    with pytest.raises(ValueError, match="Illegal transition"):
        transition(run, "complete")


def test_workflow_input_validation():
    order = WorkflowInput(
        order_id="ORD-001",
        customer_id="CUST-001",
        amount=1000,
        items=["Keyboard"],
    )

    order.validate()


def test_invalid_order_amount():
    order = WorkflowInput(
        order_id="ORD-001",
        customer_id="CUST-001",
        amount=0,
        items=["Keyboard"],
    )

    with pytest.raises(ValueError, match="positive"):
        order.validate()


def test_workflow_fixture():
    result = run_topic_fixture()

    assert result["status"] == "completed"
    assert result["run_id"] == "RUN-001"
    assert result["events"] == [
        "workflow.created",
        "start",
        "complete",
    ]


def test_workflow_cannot_transition_after_completion():
    run = create_run()

    transition(run, "start")
    transition(run, "complete")

    with pytest.raises(ValueError):
        transition(run, "start")
