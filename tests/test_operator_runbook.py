
import json
import pytest

from runbook import (
    OPERATOR_ACTIONS,
    get_operator_action,
    build_evidence_report,
    generate_runbook,
    save_evidence_report,
)


def test_operator_actions_exist():

    expected_states = {
        "created",
        "running",
        "waiting",
        "completed",
        "needs_review",
        "failed",
    }

    assert set(OPERATOR_ACTIONS.keys()) == expected_states


def test_needs_review_action():

    result = get_operator_action("needs_review")

    assert "Inspect error" in result["action"]


def test_unknown_state_rejected():

    with pytest.raises(ValueError):
        get_operator_action("unknown")


def test_evidence_report_contains_all_tasks():

    report = build_evidence_report()

    assert len(report["assessment_tasks"]) == 5

    assert report["assessment_tasks"]["task1"]["marks"] == 15
    assert report["assessment_tasks"]["task5"]["marks"] == 20


def test_evidence_files_are_listed():

    report = build_evidence_report()

    assert "outputs/task2_happy_path.json" in report["evidence_files"]
    assert "outputs/task3_recovery.json" in report["evidence_files"]
    assert "outputs/task4_observability.json" in report["evidence_files"]


def test_runbook_generation(tmp_path, monkeypatch):

    monkeypatch.chdir(tmp_path)

    path = generate_runbook()

    assert path == "reports/OPERATOR_RUNBOOK.md"

    content = (tmp_path / path).read_text(
        encoding="utf-8"
    )

    assert "Recovery procedure" in content
    assert "Security" in content


def test_evidence_report_generation(tmp_path, monkeypatch):

    monkeypatch.chdir(tmp_path)

    report = save_evidence_report()

    path = tmp_path / "reports/evidence_report.json"

    assert path.exists()

    saved = json.loads(path.read_text(encoding="utf-8"))

    assert saved["topic"] == report["topic"]
    assert saved["project"] == "Order Fulfillment Workflow"
