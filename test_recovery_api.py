
import pytest

from fastapi.testclient import TestClient

from main import app
from database import reset_database
from fault_simulator import inject_fault


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():

    reset_database()


def create_api_incident():

    inject_fault("api_degradation")

    response = client.post(
        "/workflow/api_degradation"
    )

    assert response.status_code == 200

    workflow = response.json()["workflow"]

    return workflow["recovery_plan"]["incident_id"]


# ==========================================
# TEST 1: APPROVE RECOVERY
# ==========================================

def test_approve_recovery():

    incident_id = create_api_incident()

    response = client.post(
        f"/recovery/{incident_id}/approve"
    )

    assert response.status_code == 200

    assert response.json()["recovery"]["status"] == "APPROVED"


# ==========================================
# TEST 2: REJECT RECOVERY
# ==========================================

def test_reject_recovery():

    incident_id = create_api_incident()

    response = client.post(
        f"/recovery/{incident_id}/reject"
    )

    assert response.status_code == 200

    assert response.json()["recovery"]["status"] == "REJECTED"


# ==========================================
# TEST 3: EXECUTION WITHOUT APPROVAL
# ==========================================

def test_execution_without_approval_is_blocked():

    incident_id = create_api_incident()

    response = client.post(
        f"/recovery/{incident_id}/execute"
    )

    assert response.status_code == 400

    assert "approval" in response.json()["detail"].lower()


# ==========================================
# TEST 4: EXECUTION AFTER REJECTION
# ==========================================

def test_execution_after_rejection_is_blocked():

    incident_id = create_api_incident()

    client.post(
        f"/recovery/{incident_id}/reject"
    )

    response = client.post(
        f"/recovery/{incident_id}/execute"
    )

    assert response.status_code == 400

    assert "rejected" in response.json()["detail"].lower()


# ==========================================
# TEST 5: SUCCESSFUL RECOVERY EXECUTION
# ==========================================

def test_successful_recovery_execution():

    incident_id = create_api_incident()

    client.post(
        f"/recovery/{incident_id}/approve"
    )

    response = client.post(
        f"/recovery/{incident_id}/execute"
    )

    assert response.status_code == 200

    recovery = response.json()["recovery"]

    assert recovery["status"] == "RECOVERED"

    assert recovery["verification_result"]["verified"] is True

    assert recovery["verification_result"]["checks_passed"] == 4


# ==========================================
# TEST 6: DUPLICATE EXECUTION IS BLOCKED
# ==========================================

def test_duplicate_execution_is_blocked():

    incident_id = create_api_incident()

    client.post(
        f"/recovery/{incident_id}/approve"
    )

    first_response = client.post(
        f"/recovery/{incident_id}/execute"
    )

    assert first_response.status_code == 200

    assert first_response.json()["recovery"]["status"] == "RECOVERED"

    second_response = client.post(
        f"/recovery/{incident_id}/execute"
    )

    assert second_response.status_code == 400

    assert "already been executed" in (
        second_response.json()["detail"]
    )


# ==========================================
# TEST 7: UNKNOWN INCIDENT
# ==========================================

def test_unknown_incident_returns_404():

    response = client.get(
        "/recovery/unknown-incident-id"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Recovery plan not found."
