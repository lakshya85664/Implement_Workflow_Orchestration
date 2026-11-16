
import json

from orchestrator import OrderOrchestrator
from workflow_orchestration import WorkflowInput


def test_order_fulfillment_success():

    orchestrator = OrderOrchestrator()

    order = WorkflowInput(
        order_id="TEST-2001",
        customer_id="CUST-001",
        amount=2500,
        items=["Laptop", "Mouse"],
    )

    result = orchestrator.execute(order)

    assert result.success is True
    assert result.status == "completed"

    assert result.output["payment"]["status"] == "authorized"
    assert result.output["packing"]["status"] == "packed"
    assert result.output["shipping"]["status"] == "shipment_created"


def test_validation_failure():

    orchestrator = OrderOrchestrator()

    order = WorkflowInput(
        order_id="TEST-2002",
        customer_id="CUST-002",
        amount=0,
        items=["Keyboard"],
    )

    result = orchestrator.execute(order)

    assert result.success is False
    assert "positive" in result.error
    assert result.status == "created"


def test_empty_order_validation_failure():

    orchestrator = OrderOrchestrator()

    order = WorkflowInput(
        order_id="TEST-2003",
        customer_id="CUST-003",
        amount=1000,
        items=[],
    )

    result = orchestrator.execute(order)

    assert result.success is False
    assert "at least one item" in result.error


def test_successful_order_has_all_completed_tasks():

    orchestrator = OrderOrchestrator()

    order = WorkflowInput(
        order_id="TEST-2004",
        customer_id="CUST-004",
        amount=1500,
        items=["Headphones"],
    )

    result = orchestrator.execute(order)

    assert result.success is True

    assert set(result.output["completed_tasks"]) == {
        "validate",
        "payment",
        "packing",
        "shipping",
    }


def test_invalid_order_does_not_process_payment():

    orchestrator = OrderOrchestrator()

    order = WorkflowInput(
        order_id="TEST-2005",
        customer_id="CUST-005",
        amount=-100,
        items=["Mouse"],
    )

    result = orchestrator.execute(order)

    assert result.success is False
    assert "payment" not in result.output
