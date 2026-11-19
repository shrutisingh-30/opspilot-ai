
from datetime import datetime, timezone


def collect_system_evidence():
    """
    Return a simulated system diagnostic snapshot.

    These values are controlled test data.
    They are NOT collected from a real server.
    """

    evidence = {
        "scenario_id": "database_outage_01",
        "simulated": True,
        "source": "OpsPilot Fault Simulator",
        "collected_at": datetime.now(timezone.utc).isoformat(),

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
            "recent_deployment_detected": False,
            "observation": "No recent deployment detected"
        },

        "services": {
            "database_service": "UNHEALTHY",
            "payment_service": "DEGRADED"
        }
    }

    return evidence
