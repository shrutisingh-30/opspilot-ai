
from uuid import uuid4
from copy import deepcopy

from database import (
    save_recovery_plan,
    update_recovery_plan,
    get_recovery_plan_from_db,
    log_audit_event
)

from fault_simulator import (
    SCENARIOS,
    create_initial_system_state,
    get_simulated_system_state,
    update_simulated_system_state
)


# ==================================================
# OPSPILOT AI - RECOVERY ENGINE
# ==================================================

# All recovery actions are simulated.
# No real production infrastructure is modified.


# ==================================================
# RECOVERY ACTION DEFINITIONS
# ==================================================

RECOVERY_ACTIONS = {

    "DATABASE_CONNECTIVITY_FAILURE": {
        "action": "RESTORE_DATABASE_CONNECTIVITY",
        "description": "Simulate restoring database connectivity",

        "verification": {
            "database_status": "UP",
            "database_service_status": "HEALTHY",
            "payment_service_status": "HEALTHY",
            "payment_api_status": "HEALTHY",
            "error_rate_percent": 0,
            "p95_response_time_ms": 150
        }
    },

    "API_PERFORMANCE_DEGRADATION": {
        "action": "RESTART_PAYMENT_API",
        "description": "Simulate restarting the payment API",

        "verification": {
            "payment_api_status": "HEALTHY",
            "payment_service_status": "HEALTHY",
            "error_rate_percent": 0,
            "p95_response_time_ms": 150
        }
    },

    "RESOURCE_EXHAUSTION": {
        "action": "RELEASE_EXCESS_MEMORY",
        "description": "Simulate releasing excess application memory",

        "verification": {
            "memory_usage_percent": 45,
            "cpu_usage_percent": 40,
            "payment_service_status": "HEALTHY",
            "payment_api_status": "HEALTHY",
            "error_rate_percent": 0,
            "p95_response_time_ms": 150
        }
    },

    "DEPLOYMENT_REGRESSION": {
        "action": "ROLLBACK_DEPLOYMENT",
        "description": "Simulate rolling back to the previous deployment",

        "verification": {
            "deployment_rolled_back": True,
            "payment_service_status": "HEALTHY",
            "payment_api_status": "HEALTHY",
            "error_rate_percent": 0,
            "p95_response_time_ms": 150
        }
    }
}


# ==================================================
# FUNCTION 1: CREATE RECOVERY PLAN
# ==================================================

def create_recovery_plan(scenario_id, investigation):

    if not investigation.get("incident_detected"):

        return {
            "status": "NO_RECOVERY_REQUIRED",
            "message": "No incident detected. Recovery is unnecessary."
        }

    root_cause = investigation.get("suspected_root_cause")

    if root_cause not in RECOVERY_ACTIONS:

        return {
            "status": "NO_SAFE_ACTION",
            "message": "No approved recovery action exists for this diagnosis."
        }

    if scenario_id not in SCENARIOS:

        raise ValueError(f"Unknown scenario: {scenario_id}")

    # Ensure that an initial system state exists.

    try:
        get_simulated_system_state(scenario_id)

    except ValueError:

        initial_state = create_initial_system_state(
            SCENARIOS[scenario_id]["evidence"]
        )

        update_simulated_system_state(
            scenario_id,
            initial_state
        )

    action_details = RECOVERY_ACTIONS[root_cause]

    incident_id = str(uuid4())

    plan = {
        "incident_id": incident_id,
        "scenario_id": scenario_id,
        "root_cause": root_cause,
        "proposed_action": action_details["action"],
        "description": action_details["description"],

        "expected_outcome": deepcopy(
            action_details["verification"]
        ),

        "status": "PENDING_APPROVAL",
        "human_approval_required": True,
        "execution_result": None,
        "verification_result": None
    }

    save_recovery_plan(plan)

    log_audit_event(
        incident_id,
        "HUMAN_APPROVAL_REQUIRED",
        {
            "required": True
        }
    )

    return get_recovery_plan_from_db(incident_id)


# ==================================================
# FUNCTION 2: APPROVE RECOVERY
# ==================================================

def approve_recovery(incident_id):

    plan = get_recovery_plan_from_db(incident_id)

    if plan["status"] != "PENDING_APPROVAL":

        raise ValueError(
            f"Cannot approve a plan with status: {plan['status']}"
        )

    update_recovery_plan(
        incident_id,
        {
            "status": "APPROVED"
        }
    )

    log_audit_event(
        incident_id,
        "RECOVERY_APPROVED",
        {
            "approved": True
        }
    )

    return get_recovery_plan_from_db(incident_id)


# ==================================================
# FUNCTION 3: REJECT RECOVERY
# ==================================================

def reject_recovery(incident_id):

    plan = get_recovery_plan_from_db(incident_id)

    if plan["status"] != "PENDING_APPROVAL":

        raise ValueError(
            f"Cannot reject a plan with status: {plan['status']}"
        )

    update_recovery_plan(
        incident_id,
        {
            "status": "REJECTED"
        }
    )

    log_audit_event(
        incident_id,
        "RECOVERY_REJECTED",
        {
            "rejected": True
        }
    )

    return get_recovery_plan_from_db(incident_id)


# ==================================================
# FUNCTION 4: APPLY SIMULATED RECOVERY ACTION
# ==================================================

def apply_recovery_action(plan, current_state):

    updated_state = deepcopy(current_state)

    action = plan["proposed_action"]

    # DATABASE RECOVERY

    if action == "RESTORE_DATABASE_CONNECTIVITY":

        updated_state["database_status"] = "UP"

        updated_state["database_service_status"] = "HEALTHY"

        updated_state["payment_service_status"] = "HEALTHY"

        updated_state["payment_api_status"] = "HEALTHY"

        updated_state["error_rate_percent"] = 0

        updated_state["p95_response_time_ms"] = 150

        updated_state["active_connections"] = min(
            20,
            updated_state["max_connections"]
        )

    # API RECOVERY

    elif action == "RESTART_PAYMENT_API":

        updated_state["payment_api_status"] = "HEALTHY"

        updated_state["payment_service_status"] = "HEALTHY"

        updated_state["error_rate_percent"] = 0

        updated_state["p95_response_time_ms"] = 150

    # MEMORY RECOVERY

    elif action == "RELEASE_EXCESS_MEMORY":

        updated_state["memory_usage_percent"] = 45

        updated_state["cpu_usage_percent"] = 40

        updated_state["payment_service_status"] = "HEALTHY"

        updated_state["payment_api_status"] = "HEALTHY"

        updated_state["error_rate_percent"] = 0

        updated_state["p95_response_time_ms"] = 150

    # DEPLOYMENT ROLLBACK

    elif action == "ROLLBACK_DEPLOYMENT":

        previous_version = updated_state.get(
            "previous_version"
        )

        if not previous_version:

            raise ValueError(
                "Previous deployment version is unavailable."
            )

        updated_state["deployment_version"] = previous_version

        updated_state["deployment_rolled_back"] = True

        updated_state["payment_service_status"] = "HEALTHY"

        updated_state["payment_api_status"] = "HEALTHY"

        updated_state["error_rate_percent"] = 0

        updated_state["p95_response_time_ms"] = 150

    else:

        raise ValueError(
            f"Unsupported recovery action: {action}"
        )

    updated_state["last_recovery_action"] = action

    return updated_state


# ==================================================
# FUNCTION 5: INDEPENDENTLY VERIFY RECOVERY
# ==================================================

def verify_recovery(scenario_id, expected_outcome):

    # Read the saved state independently from SQLite.
    # Do not trust the execution result as proof of success.

    actual_state = get_simulated_system_state(
        scenario_id
    )

    failed_checks = []
    passed_checks = []

    # Compare every expected recovery condition.

    for key, expected_value in expected_outcome.items():

        actual_value = actual_state.get(key)

        if actual_value == expected_value:

            passed_checks.append({
                "field": key,
                "expected": expected_value,
                "actual": actual_value,
                "passed": True
            })

        else:

            failed_checks.append({
                "field": key,
                "expected": expected_value,
                "actual": actual_value,
                "passed": False
            })

    verified = len(failed_checks) == 0

    return {

        "verified": verified,

        "checks_passed": len(passed_checks),

        "checks_failed": len(failed_checks),

        "passed_checks": passed_checks,

        "failed_checks": failed_checks,

        "observed_system_state": actual_state,

        "message": (
            "All recovery conditions verified."
            if verified
            else "Recovery verification failed. "
                 "One or more expected conditions were not satisfied."
        )
    }


# ==================================================
# FUNCTION 6: EXECUTE RECOVERY
# ==================================================


# ==================================================
# FUNCTION 6: EXECUTE RECOVERY
# ==================================================

def execute_recovery(incident_id):

    plan = get_recovery_plan_from_db(incident_id)

    current_status = plan["status"]

    # ----------------------------------------------
    # STEP 1: VALIDATE RECOVERY PLAN STATUS
    # ----------------------------------------------

    if current_status == "PENDING_APPROVAL":

        raise ValueError(
            "Human approval is required before recovery execution."
        )

    elif current_status == "REJECTED":

        raise ValueError(
            "Recovery execution blocked. This recovery plan was rejected."
        )

    elif current_status == "RECOVERED":

        raise ValueError(
            "Recovery has already been executed and verified successfully."
        )

    elif current_status == "RECOVERY_FAILED":

        raise ValueError(
            "Recovery previously failed. Manual review is required before retrying."
        )

    elif current_status != "APPROVED":

        raise ValueError(
            f"Recovery execution is not allowed for status: {current_status}"
        )

    # ----------------------------------------------
    # STEP 2: READ SYSTEM STATE BEFORE EXECUTION
    # ----------------------------------------------

    scenario_id = plan["scenario_id"]

    before_state = get_simulated_system_state(
        scenario_id
    )

    # ----------------------------------------------
    # STEP 3: APPLY SIMULATED RECOVERY ACTION
    # ----------------------------------------------

    updated_state = apply_recovery_action(
        plan,
        before_state
    )

    # ----------------------------------------------
    # STEP 4: SAVE UPDATED SYSTEM STATE
    # ----------------------------------------------

    update_simulated_system_state(
        scenario_id,
        updated_state
    )

    execution_result = {

        "executed": True,

        "mode": "SIMULATION",

        "action": plan["proposed_action"],

        "message": "Simulated recovery action executed.",

        "before_state": before_state,

        "after_state": updated_state
    }

    log_audit_event(
        incident_id,
        "RECOVERY_EXECUTED",
        execution_result
    )

    # ----------------------------------------------
    # STEP 5: INDEPENDENT RECOVERY VERIFICATION
    # ----------------------------------------------

    verification_result = verify_recovery(
        scenario_id,
        plan["expected_outcome"]
    )

    # ----------------------------------------------
    # STEP 6: DETERMINE FINAL STATUS
    # ----------------------------------------------

    final_status = (
        "RECOVERED"
        if verification_result["verified"]
        else "RECOVERY_FAILED"
    )

    update_recovery_plan(
        incident_id,
        {
            "execution_result": execution_result,
            "verification_result": verification_result,
            "status": final_status
        }
    )

    # ----------------------------------------------
    # STEP 7: RECORD VERIFICATION IN AUDIT HISTORY
    # ----------------------------------------------

    log_audit_event(
        incident_id,
        "RECOVERY_VERIFIED",
        verification_result
    )

    return get_recovery_plan_from_db(
        incident_id
    )

# ==================================================
# FUNCTION 7: GET RECOVERY PLAN
# ==================================================

def get_recovery_plan(incident_id):

    return get_recovery_plan_from_db(
        incident_id
    )
