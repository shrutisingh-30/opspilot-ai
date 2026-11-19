
import pytest

from recovery_engine import (
    create_recovery_plan,
    approve_recovery,
    reject_recovery,
    execute_recovery,
    get_recovery_plan
)

from database import (
    reset_database,
    get_audit_history,
    list_recovery_plans
)


@pytest.fixture(autouse=True)
def clean_database():
    reset_database()


def sample_investigation():
    return {
        "incident_detected": True,
        "suspected_root_cause": "DATABASE_CONNECTIVITY_FAILURE"
    }


def test_recovery_plan_is_created():
    plan = create_recovery_plan(
        "database_outage",
        sample_investigation()
    )
    assert plan["status"] == "PENDING_APPROVAL"


def test_healthy_system_does_not_need_recovery():
    result = create_recovery_plan(
        "healthy_system",
        {
            "incident_detected": False,
            "suspected_root_cause": "UNKNOWN"
        }
    )
    assert result["status"] == "NO_RECOVERY_REQUIRED"


def test_recovery_cannot_execute_without_approval():
    plan = create_recovery_plan(
        "database_outage",
        sample_investigation()
    )

    with pytest.raises(ValueError):
        execute_recovery(plan["incident_id"])


def test_recovery_requires_approval_before_execution():
    plan = create_recovery_plan(
        "database_outage",
        sample_investigation()
    )

    approve_recovery(plan["incident_id"])

    result = execute_recovery(plan["incident_id"])

    assert result["status"] == "RECOVERED"


def test_recovery_can_be_rejected():
    plan = create_recovery_plan(
        "database_outage",
        sample_investigation()
    )

    result = reject_recovery(plan["incident_id"])

    assert result["status"] == "REJECTED"


def test_rejected_recovery_cannot_execute():
    plan = create_recovery_plan(
        "database_outage",
        sample_investigation()
    )

    reject_recovery(plan["incident_id"])

    with pytest.raises(ValueError):
        execute_recovery(plan["incident_id"])


def test_recovery_status_can_be_retrieved():
    plan = create_recovery_plan(
        "database_outage",
        sample_investigation()
    )

    result = get_recovery_plan(plan["incident_id"])

    assert result["incident_id"] == plan["incident_id"]


def test_unknown_incident_is_rejected():
    with pytest.raises(ValueError):
        get_recovery_plan("invalid-incident-id")


def test_recovery_plan_is_persisted():
    plan = create_recovery_plan(
        "database_outage",
        sample_investigation()
    )

    stored = get_recovery_plan(plan["incident_id"])

    assert stored["incident_id"] == plan["incident_id"]


def test_approval_is_recorded_in_audit_history():
    plan = create_recovery_plan(
        "database_outage",
        sample_investigation()
    )

    approve_recovery(plan["incident_id"])

    history = get_audit_history(plan["incident_id"])

    event_types = [event["event_type"] for event in history]

    assert "PLAN_CREATED" in event_types
    assert "RECOVERY_APPROVED" in event_types


def test_execution_and_verification_are_audited():
    plan = create_recovery_plan(
        "database_outage",
        sample_investigation()
    )

    approve_recovery(plan["incident_id"])
    execute_recovery(plan["incident_id"])

    history = get_audit_history(plan["incident_id"])

    event_types = [event["event_type"] for event in history]

    assert "RECOVERY_EXECUTED" in event_types
    assert "RECOVERY_VERIFIED" in event_types


def test_recovery_plan_list():
    create_recovery_plan(
        "database_outage",
        sample_investigation()
    )

    plans = list_recovery_plans()

    assert len(plans) == 1
