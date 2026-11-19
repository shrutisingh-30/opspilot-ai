
from datetime import datetime, timezone, timedelta
from copy import deepcopy

from database import (
    save_system_state,
    get_system_state,
    update_system_state
)


# ==================================================
# OPSPILOT AI - FAULT INJECTION SIMULATOR
# ==================================================

SCENARIOS = {

    # SCENARIO 1: DATABASE OUTAGE

    "database_outage": {

        "description": "Database connectivity failure",

        "ground_truth": "DATABASE_CONNECTIVITY_FAILURE",

        "logs": [
            "ERROR Database connection failed",
            "ERROR Payment API timeout",
            "ERROR Database connection failed",
            "ERROR Payment processing failed"
        ],

        "evidence": {

            "database": {
                "status": "DOWN",
                "active_connections": 50,
                "max_connections": 50,
                "failed_connections_last_5m": 18
            },

            "payment_api": {
                "status": "DEGRADED",
                "p95_response_time_ms": 4200,
                "error_rate_percent": 35
            },

            "resources": {
                "cpu_usage_percent": 38,
                "memory_usage_percent": 72
            },

            "deployment": {
                "recent_deployment_detected": False
            },

            "services": {
                "database_service": "UNHEALTHY",
                "payment_service": "DEGRADED"
            }
        }
    },


    # SCENARIO 2: API PERFORMANCE DEGRADATION

    "api_degradation": {

        "description": "Payment API performance degradation",

        "ground_truth": "API_PERFORMANCE_DEGRADATION",

        "logs": [
            "WARNING Payment API response time is high",
            "ERROR Payment API timeout",
            "ERROR Payment API request failed"
        ],

        "evidence": {

            "database": {
                "status": "UP",
                "active_connections": 20,
                "max_connections": 100,
                "failed_connections_last_5m": 0
            },

            "payment_api": {
                "status": "DEGRADED",
                "p95_response_time_ms": 5500,
                "error_rate_percent": 42
            },

            "resources": {
                "cpu_usage_percent": 45,
                "memory_usage_percent": 60
            },

            "deployment": {
                "recent_deployment_detected": False
            },

            "services": {
                "database_service": "HEALTHY",
                "payment_service": "DEGRADED"
            }
        }
    },


    # SCENARIO 3: MEMORY EXHAUSTION

    "memory_exhaustion": {

        "description": "Application memory exhaustion",

        "ground_truth": "RESOURCE_EXHAUSTION",

        "logs": [
            "WARNING Memory usage is high",
            "ERROR Application out of memory",
            "ERROR Payment service restarted"
        ],

        "evidence": {

            "database": {
                "status": "UP",
                "active_connections": 25,
                "max_connections": 100,
                "failed_connections_last_5m": 0
            },

            "payment_api": {
                "status": "DEGRADED",
                "p95_response_time_ms": 2800,
                "error_rate_percent": 20
            },

            "resources": {
                "cpu_usage_percent": 85,
                "memory_usage_percent": 97
            },

            "deployment": {
                "recent_deployment_detected": False
            },

            "services": {
                "database_service": "HEALTHY",
                "payment_service": "UNHEALTHY"
            }
        }
    },


    # SCENARIO 4: DEPLOYMENT REGRESSION

    "deployment_regression": {

        "description": "Recent deployment caused service degradation",

        "ground_truth": "DEPLOYMENT_REGRESSION",

        "logs": [
            "INFO Deployment v2.1.0 completed",
            "ERROR Payment API timeout",
            "ERROR Payment processing failed"
        ],

        "evidence": {

            "database": {
                "status": "UP",
                "active_connections": 30,
                "max_connections": 100,
                "failed_connections_last_5m": 0
            },

            "payment_api": {
                "status": "DEGRADED",
                "p95_response_time_ms": 3500,
                "error_rate_percent": 30
            },

            "resources": {
                "cpu_usage_percent": 40,
                "memory_usage_percent": 65
            },

            "deployment": {
                "recent_deployment_detected": True,
                "minutes_since_deployment": 3,
                "version": "v2.1.0",
                "previous_version": "v2.0.9"
            },

            "services": {
                "database_service": "HEALTHY",
                "payment_service": "DEGRADED"
            }
        }
    },


    # SCENARIO 5: HEALTHY SYSTEM

    "healthy_system": {

        "description": "All services operating normally",

        "ground_truth": "NO_INCIDENT",

        "logs": [
            "INFO Payment service operating normally",
            "INFO Database connection successful",
            "INFO Health check completed"
        ],

        "evidence": {

            "database": {
                "status": "UP",
                "active_connections": 20,
                "max_connections": 100,
                "failed_connections_last_5m": 0
            },

            "payment_api": {
                "status": "HEALTHY",
                "p95_response_time_ms": 150,
                "error_rate_percent": 0
            },

            "resources": {
                "cpu_usage_percent": 25,
                "memory_usage_percent": 45
            },

            "deployment": {
                "recent_deployment_detected": False
            },

            "services": {
                "database_service": "HEALTHY",
                "payment_service": "HEALTHY"
            }
        }
    }

}


# ==================================================
# FUNCTION 1: LIST AVAILABLE SCENARIOS
# ==================================================

def list_scenarios():

    available_scenarios = []

    for scenario_id, scenario in SCENARIOS.items():

        available_scenarios.append({
            "scenario_id": scenario_id,
            "description": scenario["description"]
        })

    return available_scenarios


# ==================================================
# FUNCTION 2: CREATE INITIAL SIMULATED SYSTEM STATE
# ==================================================

def create_initial_system_state(evidence):

    return {

        "database_status": evidence["database"]["status"],

        "database_service_status": (
            evidence["services"]["database_service"]
        ),

        "payment_api_status": (
            evidence["payment_api"]["status"]
        ),

        "payment_service_status": (
            evidence["services"]["payment_service"]
        ),

        "error_rate_percent": (
            evidence["payment_api"]["error_rate_percent"]
        ),

        "p95_response_time_ms": (
            evidence["payment_api"]["p95_response_time_ms"]
        ),

        "memory_usage_percent": (
            evidence["resources"]["memory_usage_percent"]
        ),

        "cpu_usage_percent": (
            evidence["resources"]["cpu_usage_percent"]
        ),

        "active_connections": (
            evidence["database"]["active_connections"]
        ),

        "max_connections": (
            evidence["database"]["max_connections"]
        ),

        "deployment_rolled_back": False,

        "deployment_version": (
            evidence["deployment"].get("version")
        ),

        "previous_version": (
            evidence["deployment"].get("previous_version")
        ),

        "simulated": True,

        "last_recovery_action": None
    }


# ==================================================
# FUNCTION 3: INJECT A FAILURE SCENARIO
# ==================================================

def inject_fault(scenario_id):

    if scenario_id not in SCENARIOS:

        raise ValueError(
            f"Unknown scenario: {scenario_id}"
        )

    scenario = deepcopy(SCENARIOS[scenario_id])

    base_time = datetime.now(timezone.utc)

    timestamped_logs = []

    for index, message in enumerate(scenario["logs"]):

        event_time = base_time + timedelta(
            seconds=index * 2
        )

        timestamp = event_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        timestamped_logs.append(
            f"{timestamp} {message}"
        )

    # Create the initial state from scenario evidence.

    initial_state = create_initial_system_state(
        scenario["evidence"]
    )

    # Persist the initial state in SQLite.
    # Injecting the same scenario again resets its state.

    save_system_state(
        scenario_id,
        initial_state
    )

    return {

        "scenario_id": scenario_id,

        "description": scenario["description"],

        "simulated": True,

        "source": "OpsPilot Fault Simulator",

        "injected_at": base_time.isoformat(),

        # Ground truth is for evaluation only.
        # Never pass it to the RCA engine.

        "ground_truth": scenario["ground_truth"],

        "logs": timestamped_logs,

        "evidence": scenario["evidence"],

        "system_state": deepcopy(initial_state)

    }


# ==================================================
# FUNCTION 4: GET SCENARIO GROUND TRUTH
# ==================================================

def get_ground_truth(scenario_id):

    if scenario_id not in SCENARIOS:

        raise ValueError(
            f"Unknown scenario: {scenario_id}"
        )

    return SCENARIOS[scenario_id]["ground_truth"]


# ==================================================
# FUNCTION 5: GET SCENARIO COUNT
# ==================================================

def get_scenario_count():

    return len(SCENARIOS)


# ==================================================
# FUNCTION 6: READ CURRENT SIMULATED SYSTEM STATE
# ==================================================

def get_simulated_system_state(scenario_id):

    if scenario_id not in SCENARIOS:

        raise ValueError(
            f"Unknown scenario: {scenario_id}"
        )

    return get_system_state(scenario_id)


# ==================================================
# FUNCTION 7: UPDATE SIMULATED SYSTEM STATE
# ==================================================

def update_simulated_system_state(scenario_id, new_state):

    if scenario_id not in SCENARIOS:

        raise ValueError(
            f"Unknown scenario: {scenario_id}"
        )

    if not isinstance(new_state, dict):

        raise ValueError(
            "System state must be a dictionary."
        )

    update_system_state(
        scenario_id,
        new_state
    )
