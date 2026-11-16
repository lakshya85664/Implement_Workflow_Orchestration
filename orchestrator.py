
"""
Topic 1 - Integrated Order Orchestrator

Uses an injectable payment adapter rather than
directly implementing payment gateway behavior.
"""

from dataclasses import asdict
from pathlib import Path
import json

from workflow_orchestration import (
    WorkflowInput,
    WorkflowRun,
    WorkflowTask,
    WorkflowResult,
    transition,
)

from adapters import PaymentAdapter
from metrics import WorkflowMetrics
from observability import WorkflowObserver
from reliability import FakePaymentGateway


class OrderOrchestrator:

    def __init__(self, payment_adapter=None):

        self.max_steps = 10

        # Dependency injection.
        if payment_adapter is None:

            self.observer = WorkflowObserver()
            self.metrics = WorkflowMetrics()

            self.gateway = FakePaymentGateway()

            self.payment_adapter = PaymentAdapter(
                gateway=self.gateway,
                observer=self.observer,
                metrics=self.metrics,
            )

        else:
            self.payment_adapter = payment_adapter

    def execute(self, order: WorkflowInput) -> WorkflowResult:

        run = WorkflowRun(
            run_id=f"RUN-{order.order_id}",
            business_key=order.order_id,
            context={
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "amount": order.amount,
                "items": order.items,
            },
        )

        run.record("workflow.created")

        try:

            # Validate before any external side effect.
            order.validate()

            transition(run, "start")

            run.record("order.validation.succeeded")

            task_definitions = [
                ("validate", "Order Validation", []),
                ("payment", "Payment Processing", ["validate"]),
                ("packing", "Order Packing", ["payment"]),
                ("shipping", "Shipment Creation", ["packing"]),
            ]

            run.tasks = [
                WorkflowTask(
                    task_id=task_id,
                    name=name,
                    dependencies=dependencies,
                )
                for task_id, name, dependencies in task_definitions
            ]

            completed_tasks = set()

            for step, task in enumerate(run.tasks, start=1):

                if step > self.max_steps:
                    raise RuntimeError("Workflow step limit exceeded")

                if not all(
                    dependency in completed_tasks
                    for dependency in task.dependencies
                ):
                    raise RuntimeError(
                        f"Dependencies not satisfied: {task.task_id}"
                    )

                task.status = "running"
                task.attempts += 1

                run.record(
                    "task.started",
                    task_id=task.task_id,
                )

                # Execute individual workflow operations.
                if task.task_id == "validate":

                    task.result = {
                        "valid": True,
                        "order_id": order.order_id,
                    }

                elif task.task_id == "payment":

                    payment_response = self.payment_adapter.process_payment(
                        order_id=order.order_id,
                        amount=order.amount,
                        run_id=run.run_id,
                    )

                    # Normalize adapter response into the
                    # order orchestration domain contract.
                    task.result = {
                        **payment_response,
                        "status": "authorized",
                    }

                elif task.task_id == "packing":

                    task.result = {
                        "status": "packed",
                        "items_count": len(order.items),
                    }

                elif task.task_id == "shipping":

                    task.result = {
                        "status": "shipment_created",
                        "tracking_id": f"SHIP-{order.order_id}",
                    }

                task.status = "completed"
                completed_tasks.add(task.task_id)

                run.record(
                    "task.completed",
                    task_id=task.task_id,
                    result=task.result,
                )

            transition(run, "complete")

            output = {
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "payment": run.tasks[1].result,
                "packing": run.tasks[2].result,
                "shipping": run.tasks[3].result,
                "completed_tasks": sorted(completed_tasks),
            }

            run.record("workflow.completed")

            return WorkflowResult(
                run_id=run.run_id,
                status=run.state.value,
                success=True,
                output=output,
            )

        except Exception as exc:

            run.record(
                "workflow.execution_failed",
                error_type=type(exc).__name__,
                error=str(exc),
            )

            return WorkflowResult(
                run_id=run.run_id,
                status=run.state.value,
                success=False,
                error=str(exc),
            )


def run_demo():

    orchestrator = OrderOrchestrator()

    order = WorkflowInput(
        order_id="ORD-2001",
        customer_id="CUST-201",
        amount=4999.00,
        items=["Keyboard", "Mouse", "Monitor"],
    )

    result = orchestrator.execute(order)

    return asdict(result)


if __name__ == "__main__":

    output = run_demo()

    Path("outputs").mkdir(exist_ok=True)

    with open(
        "outputs/task2_happy_path.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(output, file, indent=4)

    print("=" * 60)
    print("INTEGRATED ORDER FULFILLMENT WORKFLOW")
    print("=" * 60)

    print(json.dumps(output, indent=4))

    print("\nEvidence saved: outputs/task2_happy_path.json")
