from database import get_audit_history
from fastapi import FastAPI, HTTPException

from recovery_engine import (
    create_recovery_plan,
    approve_recovery,
    reject_recovery,
    execute_recovery,
    get_recovery_plan
)

from evaluation_engine import run_evaluation
from rca_engine import analyze_root_cause
from evidence_engine import collect_system_evidence
from fault_simulator import inject_fault, list_scenarios

# New: Incident workflow orchestration
from incident_orchestrator import run_incident_workflow


app = FastAPI(
    title="OpsPilot AI",
    description="Evidence-Driven Autonomous Incident Investigation Platform",
    version="1.0.0"
)


# ==========================================
# 1. READ LOGS
# ==========================================

def read_logs(file_path):

    try:
        with open(file_path, "r") as file:
            return file.readlines()

    except (FileNotFoundError, PermissionError):
        return []


# ==========================================
# 2. CLASSIFY LOGS
# ==========================================

def classify_log(log):

    message = log.strip()
    lower_log = message.lower()

    category = "UNKNOWN"
    severity = "LOW"

    if "database connection failed" in lower_log:
        category = "DATABASE_FAILURE"
        severity = "CRITICAL"

    elif "deployment" in lower_log:
        category = "DEPLOYMENT_CHANGE"
        severity = "LOW"

    elif (
        "payment api" in lower_log
        or "api timeout" in lower_log
    ):
        category = "API_FAILURE"
        severity = "HIGH"

    elif (
        "memory" in lower_log
        or "out of memory" in lower_log
        or "service restarted" in lower_log
    ):
        category = "RESOURCE_ISSUE"
        severity = "HIGH" if "error" in lower_log else "MEDIUM"

    elif "payment processing failed" in lower_log:
        category = "PAYMENT_FAILURE"
        severity = "HIGH"

    elif "error" in lower_log:
        category = "GENERAL_ERROR"
        severity = "HIGH"

    elif "warning" in lower_log:
        category = "GENERAL_WARNING"
        severity = "MEDIUM"

    return {
        "message": message,
        "category": category,
        "severity": severity
    }


# ==========================================
# 3. ANALYZE LOGS
# ==========================================

def analyze_logs(logs):

    classified_logs = [
        classify_log(log)
        for log in logs
    ]

    errors = [
        log for log in classified_logs
        if log["severity"] in ["HIGH", "CRITICAL"]
    ]

    warnings = [
        log for log in classified_logs
        if "WARNING" in log["message"].upper()
    ]

    category_counts = {}

    for log in classified_logs:
        category = log["category"]

        category_counts[category] = (
            category_counts.get(category, 0) + 1
        )

    return {
        "total_entries": len(logs),
        "total_errors": len(errors),
        "total_warnings": len(warnings),
        "category_counts": category_counts,
        "classified_logs": classified_logs
    }


# ==========================================
# 4. HEALTH CHECK
# ==========================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "message": "OpsPilot AI backend is running"
    }


# ==========================================
# 5. LOG ANALYSIS
# ==========================================

@app.get("/analyze-logs")
def analyze_application_logs():

    logs = read_logs("sample_logs/application.log")

    if not logs:
        raise HTTPException(
            status_code=404,
            detail="No logs found"
        )

    return {
        "status": "success",
        "analysis": analyze_logs(logs)
    }


# ==========================================
# 6. LOG CLASSIFICATION
# ==========================================

@app.get("/classify-logs")
def classify_application_logs():

    logs = read_logs("sample_logs/application.log")

    if not logs:
        raise HTTPException(
            status_code=404,
            detail="No logs found"
        )

    return {
        "status": "success",
        "classified_logs": [
            classify_log(log)
            for log in logs
        ]
    }


# ==========================================
# 7. COLLECT SYSTEM EVIDENCE
# ==========================================

@app.get("/collect-evidence")
def get_system_evidence():

    return {
        "status": "success",
        "evidence": collect_system_evidence()
    }


# ==========================================
# 8. LIST SIMULATOR SCENARIOS
# ==========================================

@app.get("/scenarios")
def get_scenarios():

    return {
        "status": "success",
        "scenarios": list_scenarios()
    }


# ==========================================
# 9. RUN A SIMULATED INCIDENT
# ==========================================

@app.get("/simulate/{scenario_id}")
def simulate_incident(scenario_id: str):

    try:
        simulation = inject_fault(scenario_id)

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=(
                "Unknown scenario. Visit /scenarios "
                "to see available scenarios."
            )
        )

    # Ground truth is deliberately excluded from diagnosis.

    classified_logs = [
        classify_log(log)
        for log in simulation["logs"]
    ]

    investigation = analyze_root_cause(
        classified_logs,
        simulation["evidence"]
    )

    # Evaluation happens only after diagnosis.

    ground_truth = simulation["ground_truth"]
    predicted_cause = investigation["suspected_root_cause"]

    evaluation = {
        "ground_truth": ground_truth,
        "predicted_root_cause": predicted_cause,
        "correct": predicted_cause == ground_truth
    }

    return {
        "status": "success",
        "scenario_id": scenario_id,
        "description": simulation["description"],
        "simulated": True,
        "logs": simulation["logs"],
        "investigation": investigation,
        "evaluation": evaluation
    }


# ==========================================
# 10. INVESTIGATE EXISTING SAMPLE LOGS
# ==========================================

@app.get("/investigate")
def investigate_incident():

    logs = read_logs("sample_logs/application.log")

    if not logs:
        raise HTTPException(
            status_code=404,
            detail="No logs found"
        )

    classified_logs = [
        classify_log(log)
        for log in logs
    ]

    system_evidence = collect_system_evidence()

    investigation = analyze_root_cause(
        classified_logs,
        system_evidence
    )

    return {
        "status": "success",
        "investigation": investigation
    }


# ==========================================
# 11. INCIDENT WORKFLOW ORCHESTRATION
# ==========================================
from incident_orchestrator import run_incident_workflow

@app.post("/workflow/{scenario_id}")
def execute_incident_workflow(scenario_id: str):

    try:
        result = run_incident_workflow(
            scenario_id,
            classify_log,
            analyze_root_cause
        )

        return {
            "status": "success",
            "workflow": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )


# ==========================================
# 12. EVALUATE OPSPILOT
# ==========================================

@app.get("/evaluate")
def evaluate_opspilot():

    report = run_evaluation(
        classify_log,
        analyze_root_cause
    )

    return {
        "status": "success",
        "evaluation": report
    }


# ==========================================
# 13. RECOVERY PLAN ENDPOINT
# ==========================================

@app.post("/recovery/plan/{scenario_id}")
def generate_recovery_plan(scenario_id: str):

    try:
        simulation = inject_fault(scenario_id)

        classified_logs = [
            classify_log(log)
            for log in simulation["logs"]
        ]

        investigation = analyze_root_cause(
            classified_logs,
            simulation["evidence"]
        )

        plan = create_recovery_plan(
            scenario_id,
            investigation
        )

        return {
            "status": "success",
            "recovery_plan": plan
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )


# ==========================================
# 14. HUMAN APPROVAL ENDPOINT
# ==========================================

@app.post("/recovery/{incident_id}/approve")
def approve_recovery_plan(incident_id: str):

    try:
        result = approve_recovery(incident_id)

        return {
            "status": "success",
            "recovery": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ==========================================
# 15. REJECT RECOVERY ENDPOINT
# ==========================================

@app.post("/recovery/{incident_id}/reject")
def reject_recovery_plan(incident_id: str):

    try:
        result = reject_recovery(incident_id)

        return {
            "status": "success",
            "recovery": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ==========================================
# 16. EXECUTE RECOVERY ENDPOINT
# ==========================================

@app.post("/recovery/{incident_id}/execute")
def execute_recovery_plan(incident_id: str):

    try:
        result = execute_recovery(incident_id)

        return {
            "status": "success",
            "recovery": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ==========================================
# 17. GET RECOVERY STATUS ENDPOINT
# ==========================================

@app.get("/recovery/{incident_id}")
def recovery_status(incident_id: str):

    try:
        result = get_recovery_plan(incident_id)

        return {
            "status": "success",
            "recovery": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )
@app.get("/audit/{incident_id}")
def get_incident_audit_history(incident_id: str):

    history = get_audit_history(incident_id)

    if not history:
        raise HTTPException(
            status_code=404,
            detail="No audit history found for this incident."
        )

    return {
        "incident_id": incident_id,
        "total_events": len(history),
        "audit_history": history
    }