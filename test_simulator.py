
from fault_simulator import inject_fault, list_scenarios


def test_scenario_count():

    scenarios = list_scenarios()

    assert len(scenarios) == 5


def test_database_scenario():

    result = inject_fault("database_outage")

    assert result["ground_truth"] == (
        "DATABASE_CONNECTIVITY_FAILURE"
    )

    assert result["evidence"]["database"]["status"] == "DOWN"


def test_api_scenario():

    result = inject_fault("api_degradation")

    assert result["ground_truth"] == (
        "API_PERFORMANCE_DEGRADATION"
    )


def test_memory_scenario():

    result = inject_fault("memory_exhaustion")

    assert result["evidence"]["resources"]["memory_usage_percent"] == 97


def test_deployment_scenario():

    result = inject_fault("deployment_regression")

    assert result["evidence"]["deployment"]["recent_deployment_detected"] is True


def test_invalid_scenario():

    try:
        inject_fault("unknown_scenario")
        assert False, "Expected ValueError"

    except ValueError:
        assert True
