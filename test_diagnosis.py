
import pytest

from fault_simulator import inject_fault
from main import classify_log
from rca_engine import analyze_root_cause


@pytest.mark.parametrize(
    "scenario_id, expected_cause",
    [
        (
            "database_outage",
            "DATABASE_CONNECTIVITY_FAILURE"
        ),
        (
            "api_degradation",
            "API_PERFORMANCE_DEGRADATION"
        ),
        (
            "memory_exhaustion",
            "RESOURCE_EXHAUSTION"
        ),
        (
            "deployment_regression",
            "DEPLOYMENT_REGRESSION"
        )
    ]
)
def test_root_cause_diagnosis(scenario_id, expected_cause):

    simulation = inject_fault(scenario_id)

    classified_logs = [
        classify_log(log)
        for log in simulation["logs"]
    ]

    # Ground truth is deliberately NOT passed here.

    result = analyze_root_cause(
        classified_logs,
        simulation["evidence"]
    )

    assert result["suspected_root_cause"] == expected_cause
