
from main import classify_log
from rca_engine import analyze_root_cause
from evaluation_engine import run_evaluation


def test_all_scenarios_are_evaluated():

    report = run_evaluation(
        classify_log,
        analyze_root_cause
    )

    assert report["evaluation_summary"]["total_scenarios"] == 5


def test_all_predefined_scenarios_are_correct():

    report = run_evaluation(
        classify_log,
        analyze_root_cause
    )

    assert report["evaluation_summary"]["accuracy"] == 1.0


def test_no_false_positives():

    report = run_evaluation(
        classify_log,
        analyze_root_cause
    )

    assert report["incident_detection_metrics"]["false_positive"] == 0


def test_no_false_negatives():

    report = run_evaluation(
        classify_log,
        analyze_root_cause
    )

    assert report["incident_detection_metrics"]["false_negative"] == 0


def test_healthy_system_is_not_reported_as_incident():

    report = run_evaluation(
        classify_log,
        analyze_root_cause
    )

    healthy_result = next(
        result
        for result in report["scenario_results"]
        if result["scenario_id"] == "healthy_system"
    )

    assert healthy_result["predicted"] == "NO_INCIDENT"
    assert healthy_result["correct"] is True
