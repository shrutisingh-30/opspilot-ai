
import pytest

import recovery_engine

from database import reset_database
from fault_simulator import (
    inject_fault,
    get_simulated_system_state
)

from recovery_engine import (
    create_recovery_plan,
    approve_recovery,
    execute_recovery,
    verify_recovery
)


@pytest.fixture(autouse=True)
def clean_database():
    """Reset the database before every test."""
    reset_database()


RECOVERY_TEST_CASES = [
    (
        "database_outage",
        "DATABASE_CONNECTIVITY_FAILURE",
        {
            "database_status": "UP",
            "database_service_status": "HEALTHY",
            "payment_service_status": "HEALTHY"
        }
    ),
    (
        "api_degradation",
        "API_PERFORMANCE_DEGRADATION",
        {
            "payment_api_status": "HEALTHY",
            "error_rate_percent": 0
        }
    ),
    (
        "memory_exhaustion",
        "RESOURCE_EXHAUSTION",
        {
            "memory_usage_percent": 45,
            "payment_service_status": "HEALTHY"
        }
    ),
    (
        "deployment_regression",
        "DEPLOYMENT_REGRESSION",
        {
            "deployment_rolled_back": True,
            "payment_service_status": "HEALTHY",
            "payment_api_status": "HEALTHY",
            "error_rate_percent": 0
        }
    )
]


@pytest.mark.parametrize(
    "scenario_id, root_cause, expected_state",
    RECOVERY_TEST_CASES
)
def test_recovery_succeeds_for_all_scenarios(
    scenario_id,
    root_cause,
    expected_state
):
    """Test that all four recovery actions work correctly."""

    # Step 1: Inject the simulated incident.
    inject_fault(scenario_id)

    # Step 2: Prepare an investigation result.
    investigation = {
        "incident_detected": True,
        "suspected_root_cause": root_cause
    }

    # Step 3: Create a recovery plan.
    plan = create_recovery_plan(scenario_id, investigation)

    assert plan["status"] == "PENDING_APPROVAL"

    # Step 4: Approve the recovery plan.
    approved_plan = approve_recovery(plan["incident_id"])

    assert approved_plan["status"] == "APPROVED"

    # Step 5: Execute recovery.
    result = execute_recovery(plan["incident_id"])

    assert result["status"] == "RECOVERED"

    # Step 6: Read the actual persisted system state.
    actual_state = get_simulated_system_state(scenario_id)

    # Step 7: Confirm that the expected state changes occurred.
    for key, expected_value in expected_state.items():
        assert actual_state[key] == expected_value


def test_independent_verifier_detects_successful_recovery():
    """Test that the verifier confirms the expected system state."""

    scenario_id = "database_outage"

    inject_fault(scenario_id)

    # Initially, the database should be down.
    initial_state = get_simulated_system_state(scenario_id)

    assert initial_state["database_status"] == "DOWN"

    # Apply a successful recovery.
    investigation = {
        "incident_detected": True,
        "suspected_root_cause": "DATABASE_CONNECTIVITY_FAILURE"
    }

    plan = create_recovery_plan(scenario_id, investigation)

    approve_recovery(plan["incident_id"])

    result = execute_recovery(plan["incident_id"])

    assert result["status"] == "RECOVERED"

    # Independently verify the persisted state.
    verification = verify_recovery(
        scenario_id,
        {
            "database_status": "UP",
            "database_service_status": "HEALTHY",
            "payment_service_status": "HEALTHY"
        }
    )

    assert verification["verified"] is True
    assert verification["failed_checks"] == []


def test_independent_verifier_detects_failed_recovery():
    """Test that the verifier rejects an incorrect system state."""

    scenario_id = "database_outage"

    inject_fault(scenario_id)

    # The initial database state is DOWN.
    verification = verify_recovery(
        scenario_id,
        {
            "database_status": "UP"
        }
    )

    assert verification["verified"] is False
    assert len(verification["failed_checks"]) > 0


def test_execution_reports_failure_when_recovery_does_not_work(
    monkeypatch
):
    """Test that execution does not falsely report successful recovery."""

    scenario_id = "database_outage"

    inject_fault(scenario_id)

    investigation = {
        "incident_detected": True,
        "suspected_root_cause": "DATABASE_CONNECTIVITY_FAILURE"
    }

    plan = create_recovery_plan(scenario_id, investigation)

    approve_recovery(plan["incident_id"])

    # Simulate a recovery action that makes no changes.
    def failed_recovery_action(plan, current_state):
        return current_state.copy()

    monkeypatch.setattr(
        recovery_engine,
        "apply_recovery_action",
        failed_recovery_action
    )

    result = execute_recovery(plan["incident_id"])

    # The independent verifier should catch the failure.
    assert result["status"] == "RECOVERY_FAILED"
    assert result["verification_result"]["verified"] is False


def test_duplicate_recovery_execution_is_blocked():

    # 1. Inject an API degradation fault
    inject_fault("api_degradation")

    # 2. Create a recovery plan
    investigation = {
        "incident_detected": True,
        "suspected_root_cause": "API_PERFORMANCE_DEGRADATION"
    }

    plan = create_recovery_plan(
        "api_degradation",
        investigation
    )

    incident_id = plan["incident_id"]

    # 3. Approve the recovery plan
    approve_recovery(incident_id)

    # 4. Execute recovery for the first time
    result = execute_recovery(incident_id)

    assert result["status"] == "RECOVERED"

    # 5. Attempt execution for the second time
    with pytest.raises(
        ValueError,
        match="already been executed"
    ):
        execute_recovery(incident_id)
