
import sqlite3
import json

from pathlib import Path
from datetime import datetime, timezone


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DATABASE_PATH = Path(__file__).resolve().parent / "opspilot.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    # Enable foreign key enforcement
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

def init_db():

    connection = get_connection()
    cursor = connection.cursor()

    # Recovery plans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recovery_plans (
            incident_id TEXT PRIMARY KEY,
            scenario_id TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            proposed_action TEXT NOT NULL,
            description TEXT,
            expected_outcome TEXT,
            status TEXT NOT NULL,
            human_approval_required INTEGER NOT NULL,
            execution_result TEXT,
            verification_result TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Audit history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL,

            FOREIGN KEY (incident_id)
            REFERENCES recovery_plans (incident_id)
        )
    """)

    # Simulated system state table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_states (
            scenario_id TEXT PRIMARY KEY,
            state_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# --------------------------------------------------
# RECOVERY PLAN OPERATIONS
# --------------------------------------------------

def save_recovery_plan(plan):

    connection = get_connection()
    timestamp = current_timestamp()

    connection.execute("""
        INSERT INTO recovery_plans (
            incident_id,
            scenario_id,
            root_cause,
            proposed_action,
            description,
            expected_outcome,
            status,
            human_approval_required,
            execution_result,
            verification_result,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        plan["incident_id"],
        plan["scenario_id"],
        plan["root_cause"],
        plan["proposed_action"],
        plan["description"],
        json.dumps(plan["expected_outcome"]),
        plan["status"],
        int(plan["human_approval_required"]),
        None,
        None,
        timestamp,
        timestamp
    ))

    connection.commit()
    connection.close()

    log_audit_event(
        plan["incident_id"],
        "PLAN_CREATED",
        {"status": plan["status"]}
    )


def update_recovery_plan(incident_id, updates):

    allowed_fields = {
        "status",
        "execution_result",
        "verification_result"
    }

    for field in updates:
        if field not in allowed_fields:
            raise ValueError(f"Invalid update field: {field}")

    if not updates:
        return

    assignments = []
    values = []

    for field, value in updates.items():

        assignments.append(f"{field} = ?")

        if field in {
            "execution_result",
            "verification_result"
        }:
            value = json.dumps(value)

        values.append(value)

    assignments.append("updated_at = ?")
    values.append(current_timestamp())
    values.append(incident_id)

    connection = get_connection()

    cursor = connection.execute(
        f"""
        UPDATE recovery_plans
        SET {", ".join(assignments)}
        WHERE incident_id = ?
        """,
        values
    )

    connection.commit()
    updated = cursor.rowcount
    connection.close()

    if updated == 0:
        raise ValueError("Recovery plan not found.")


def get_recovery_plan_from_db(incident_id):

    connection = get_connection()

    row = connection.execute("""
        SELECT *
        FROM recovery_plans
        WHERE incident_id = ?
    """, (incident_id,)).fetchone()

    connection.close()

    if row is None:
        raise ValueError("Recovery plan not found.")

    result = dict(row)

    result["expected_outcome"] = json.loads(
        result["expected_outcome"]
    )

    result["execution_result"] = (
        json.loads(result["execution_result"])
        if result["execution_result"]
        else None
    )

    result["verification_result"] = (
        json.loads(result["verification_result"])
        if result["verification_result"]
        else None
    )

    result["human_approval_required"] = bool(
        result["human_approval_required"]
    )

    return result


def list_recovery_plans():

    connection = get_connection()

    rows = connection.execute("""
        SELECT
            incident_id,
            scenario_id,
            root_cause,
            proposed_action,
            status,
            created_at,
            updated_at
        FROM recovery_plans
        ORDER BY created_at DESC
    """).fetchall()

    connection.close()

    return [dict(row) for row in rows]


# --------------------------------------------------
# AUDIT LOG OPERATIONS
# --------------------------------------------------

def log_audit_event(incident_id, event_type, details=None):

    connection = get_connection()

    connection.execute("""
        INSERT INTO audit_events (
            incident_id,
            event_type,
            details,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        incident_id,
        event_type,
        json.dumps(details or {}),
        current_timestamp()
    ))

    connection.commit()
    connection.close()


def get_audit_history(incident_id):

    connection = get_connection()

    rows = connection.execute("""
        SELECT
            event_id,
            incident_id,
            event_type,
            details,
            created_at
        FROM audit_events
        WHERE incident_id = ?
        ORDER BY event_id ASC
    """, (incident_id,)).fetchall()

    connection.close()

    history = []

    for row in rows:

        event = dict(row)

        event["details"] = json.loads(
            event["details"]
        )

        history.append(event)

    return history


# --------------------------------------------------
# SYSTEM STATE OPERATIONS
# --------------------------------------------------

def save_system_state(scenario_id, state):

    connection = get_connection()

    connection.execute("""
        INSERT OR REPLACE INTO system_states (
            scenario_id,
            state_json,
            updated_at
        )
        VALUES (?, ?, ?)
    """, (
        scenario_id,
        json.dumps(state),
        current_timestamp()
    ))

    connection.commit()
    connection.close()


def get_system_state(scenario_id):

    connection = get_connection()

    row = connection.execute("""
        SELECT state_json
        FROM system_states
        WHERE scenario_id = ?
    """, (scenario_id,)).fetchone()

    connection.close()

    if row is None:
        raise ValueError("System state not found.")

    return json.loads(row["state_json"])


def update_system_state(scenario_id, state):

    save_system_state(scenario_id, state)


# --------------------------------------------------
# TESTING UTILITY
# --------------------------------------------------

def reset_database():
    """
    Used only by automated tests.
    Clears recovery plans, audit events and system states.
    """

    connection = get_connection()

    connection.execute("DELETE FROM audit_events")
    connection.execute("DELETE FROM recovery_plans")
    connection.execute("DELETE FROM system_states")

    connection.commit()
    connection.close()


# --------------------------------------------------
# INITIALIZE DATABASE
# --------------------------------------------------

init_db()
