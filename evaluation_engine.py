
from fault_simulator import inject_fault, list_scenarios


def run_evaluation(classifier, diagnosis_engine):

    results = []

    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0

    correct_predictions = 0

    for scenario in list_scenarios():

        scenario_id = scenario["scenario_id"]

        # Generate simulated incident
        simulation = inject_fault(scenario_id)

        # Classify logs
        classified_logs = [
            classifier(log)
            for log in simulation["logs"]
        ]

        # Diagnose using logs and evidence only
        investigation = diagnosis_engine(
            classified_logs,
            simulation["evidence"]
        )

        # Compare diagnosis with ground truth
        actual = simulation["ground_truth"]

        if investigation["incident_detected"]:
            predicted = investigation["suspected_root_cause"]
        else:
            predicted = "NO_INCIDENT"

        correct = predicted == actual

        if correct:
            correct_predictions += 1

        actual_incident = actual != "NO_INCIDENT"
        predicted_incident = investigation["incident_detected"]

        if actual_incident and predicted_incident:
            true_positive += 1

        elif not actual_incident and predicted_incident:
            false_positive += 1

        elif not actual_incident and not predicted_incident:
            true_negative += 1

        elif actual_incident and not predicted_incident:
            false_negative += 1

        results.append({
            "scenario_id": scenario_id,
            "actual": actual,
            "predicted": predicted,
            "correct": correct,
            "diagnosis_status": investigation["diagnosis_status"]
        })

    total = len(results)

    accuracy = (
        correct_predictions / total
        if total else 0
    )

    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive) else 0
    )

    recall = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative) else 0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) else 0
    )

    return {
        "evaluation_summary": {
            "total_scenarios": total,
            "correct_predictions": correct_predictions,
            "incorrect_predictions": total - correct_predictions,
            "accuracy": round(accuracy, 4)
        },

        "incident_detection_metrics": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4)
        },

        "scenario_results": results,

        "evaluation_note": (
            "Metrics are calculated on predefined simulated "
            "scenarios. They do not represent real-world "
            "incident detection performance."
        )
    }
