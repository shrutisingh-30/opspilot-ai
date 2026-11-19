
from fault_simulator import inject_fault

from recovery_engine import create_recovery_plan


def run_incident_workflow(
    scenario_id,
    classifier,
    diagnosis_engine
):
    """
    Runs the incident investigation workflow.

    Steps:
    1. Inject a simulated incident.
    2. Collect logs and evidence.
    3. Classify logs.
    4. Investigate the root cause.
    5. Generate a recovery plan.
    6. Wait for human approval.

    Recovery is NOT executed automatically.
    """

    # STEP 1: Inject the incident and collect evidence.
    simulation = inject_fault(scenario_id)

    logs = simulation["logs"]
    evidence = simulation["evidence"]

    # STEP 2: Classify every log.
    classified_logs = [
        classifier(log)
        for log in logs
    ]

    # STEP 3: Investigate the incident.
    investigation = diagnosis_engine(
        classified_logs,
        evidence
    )

    # STEP 4: Generate a recovery plan.
    recovery_plan = create_recovery_plan(
        scenario_id,
        investigation
    )

    # STEP 5: Determine the workflow status.
    if not investigation.get("incident_detected"):
        workflow_status = "NO_INCIDENT"

    elif recovery_plan.get("status") == "PENDING_APPROVAL":
        workflow_status = "AWAITING_HUMAN_APPROVAL"

    else:
        workflow_status = "RECOVERY_PLAN_UNAVAILABLE"

    # STEP 6: Return the complete investigation result.
    return {
        "scenario_id": scenario_id,
        "simulated": True,

        "workflow_status": workflow_status,

        "evidence": evidence,

        "logs": logs,

        "classified_logs": classified_logs,

        "investigation": investigation,

        "recovery_plan": recovery_plan,

        "human_approval_required": (
            recovery_plan.get("human_approval_required", False)
        ),

        "recovery_executed": False,

        "message": (
            "Incident investigation completed. "
            "Human approval is required before recovery execution."
            if workflow_status == "AWAITING_HUMAN_APPROVAL"
            else "Incident workflow completed."
        )
    }
