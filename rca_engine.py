
from datetime import datetime


ROOT_CAUSES = [
    "DATABASE_CONNECTIVITY_FAILURE",
    "API_PERFORMANCE_DEGRADATION",
    "RESOURCE_EXHAUSTION",
    "DEPLOYMENT_REGRESSION"
]


def parse_timestamp(log_message):

    try:
        return datetime.strptime(
            log_message[:19],
            "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        return None


def analyze_root_cause(classified_logs, system_evidence=None):

    evidence = system_evidence or {}

    database = evidence.get("database", {})
    api = evidence.get("payment_api", {})
    resources = evidence.get("resources", {})
    deployment = evidence.get("deployment", {})
    services = evidence.get("services", {})

    # Each possible cause starts with zero points.

    scores = {
        cause: 0
        for cause in ROOT_CAUSES
    }

    reasons = {
        cause: []
        for cause in ROOT_CAUSES
    }

    categories = [
        log["category"]
        for log in classified_logs
    ]

    # --------------------------------------
    # 1. DATABASE FAILURE SIGNALS
    # --------------------------------------

    if database.get("status") == "DOWN":
        scores["DATABASE_CONNECTIVITY_FAILURE"] += 5
        reasons["DATABASE_CONNECTIVITY_FAILURE"].append(
            "Database status is DOWN."
        )

    active = database.get("active_connections")
    maximum = database.get("max_connections")

    if (
        isinstance(active, (int, float))
        and isinstance(maximum, (int, float))
        and maximum > 0
        and active >= maximum
    ):
        scores["DATABASE_CONNECTIVITY_FAILURE"] += 2
        reasons["DATABASE_CONNECTIVITY_FAILURE"].append(
            "Database connection pool is exhausted."
        )

    if database.get("failed_connections_last_5m", 0) > 0:
        scores["DATABASE_CONNECTIVITY_FAILURE"] += 2
        reasons["DATABASE_CONNECTIVITY_FAILURE"].append(
            "Recent database connection failures detected."
        )

    if "DATABASE_FAILURE" in categories:
        scores["DATABASE_CONNECTIVITY_FAILURE"] += 1
        reasons["DATABASE_CONNECTIVITY_FAILURE"].append(
            "Database failure messages found in logs."
        )

    # --------------------------------------
    # 2. API PERFORMANCE SIGNALS
    # --------------------------------------

    latency = api.get("p95_response_time_ms", 0)
    error_rate = api.get("error_rate_percent", 0)

    if isinstance(latency, (int, float)) and latency > 1000:
        scores["API_PERFORMANCE_DEGRADATION"] += 2
        reasons["API_PERFORMANCE_DEGRADATION"].append(
            "Payment API latency exceeds 1000 ms."
        )

    if isinstance(error_rate, (int, float)) and error_rate >= 20:
        scores["API_PERFORMANCE_DEGRADATION"] += 2
        reasons["API_PERFORMANCE_DEGRADATION"].append(
            "Payment API error rate is at least 20%."
        )

    if database.get("status") == "UP":
        scores["API_PERFORMANCE_DEGRADATION"] += 1
        reasons["API_PERFORMANCE_DEGRADATION"].append(
            "Database is healthy, reducing database-failure suspicion."
        )

    if "API_FAILURE" in categories:
        scores["API_PERFORMANCE_DEGRADATION"] += 1
        reasons["API_PERFORMANCE_DEGRADATION"].append(
            "API failure messages found in logs."
        )

    # --------------------------------------
    # 3. RESOURCE EXHAUSTION SIGNALS
    # --------------------------------------

    memory = resources.get("memory_usage_percent", 0)
    cpu = resources.get("cpu_usage_percent", 0)

    if isinstance(memory, (int, float)) and memory >= 90:
        scores["RESOURCE_EXHAUSTION"] += 5
        reasons["RESOURCE_EXHAUSTION"].append(
            "Memory usage is critically high."
        )

    elif isinstance(memory, (int, float)) and memory >= 80:
        scores["RESOURCE_EXHAUSTION"] += 2
        reasons["RESOURCE_EXHAUSTION"].append(
            "Memory usage is elevated."
        )

    if isinstance(cpu, (int, float)) and cpu >= 85:
        scores["RESOURCE_EXHAUSTION"] += 2
        reasons["RESOURCE_EXHAUSTION"].append(
            "CPU usage is critically high."
        )

    if services.get("payment_service") == "UNHEALTHY":
        scores["RESOURCE_EXHAUSTION"] += 1
        reasons["RESOURCE_EXHAUSTION"].append(
            "Payment service is unhealthy."
        )

    if "RESOURCE_ISSUE" in categories:
        scores["RESOURCE_EXHAUSTION"] += 1
        reasons["RESOURCE_EXHAUSTION"].append(
            "Resource-related messages found in logs."
        )

    # --------------------------------------
    # 4. DEPLOYMENT REGRESSION SIGNALS
    # --------------------------------------

    if deployment.get("recent_deployment_detected") is True:
        scores["DEPLOYMENT_REGRESSION"] += 5
        reasons["DEPLOYMENT_REGRESSION"].append(
            "A recent deployment was detected."
        )

        minutes = deployment.get("minutes_since_deployment")

        if isinstance(minutes, (int, float)) and 0 <= minutes <= 10:
            scores["DEPLOYMENT_REGRESSION"] += 2
            reasons["DEPLOYMENT_REGRESSION"].append(
                "Deployment occurred within the last 10 minutes."
            )

    if api.get("status") == "DEGRADED":
        scores["DEPLOYMENT_REGRESSION"] += 1
        reasons["DEPLOYMENT_REGRESSION"].append(
            "API degradation is present."
        )

    if "DEPLOYMENT_CHANGE" in categories:
        scores["DEPLOYMENT_REGRESSION"] += 1
        reasons["DEPLOYMENT_REGRESSION"].append(
            "Deployment event found in logs."
        )

    # --------------------------------------
    # 5. SELECT THE STRONGEST HYPOTHESIS
    # --------------------------------------

    ranked_causes = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    highest_score = ranked_causes[0][1]

    tied_causes = [
        cause
        for cause, score in ranked_causes
        if score == highest_score
    ]

    if highest_score < 3:
        diagnosis = "UNKNOWN"
        diagnosis_status = "INSUFFICIENT_EVIDENCE"

    elif len(tied_causes) > 1:
        diagnosis = "UNKNOWN"
        diagnosis_status = "AMBIGUOUS_DIAGNOSIS"

    else:
        diagnosis = ranked_causes[0][0]
        diagnosis_status = "HYPOTHESIS_SUPPORTED"

    # This is a rule score, NOT a probability.

    if highest_score >= 7 and diagnosis != "UNKNOWN":
        confidence_level = "HIGH"
    elif highest_score >= 4 and diagnosis != "UNKNOWN":
        confidence_level = "MODERATE"
    else:
        confidence_level = "LOW"

    # --------------------------------------
    # 6. RETURN INVESTIGATION REPORT
    # --------------------------------------

    return {
        "incident_detected": any(
            log["severity"] in ["HIGH", "CRITICAL"]
            for log in classified_logs
        ) or any(score >= 3 for score in scores.values()),

        "suspected_root_cause": diagnosis,

        "diagnosis_status": diagnosis_status,

        "confidence_level": confidence_level,

        "confidence_type": "rule_based_heuristic_not_probability",

        "diagnostic_scores": scores,

        "diagnostic_reasons": reasons.get(diagnosis, [])
        if diagnosis != "UNKNOWN" else [],

        "ranked_hypotheses": [
            {
                "root_cause": cause,
                "score": score
            }
            for cause, score in ranked_causes
        ],

        "system_evidence": evidence,

        "log_evidence": [
            log["message"]
            for log in classified_logs
            if log["severity"] in ["HIGH", "CRITICAL"]
        ],

        "explanation": (
            f"The strongest supported hypothesis is {diagnosis}."
            if diagnosis != "UNKNOWN"
            else "The available evidence is insufficient or conflicting. "
                 "OpsPilot cannot confidently select one root cause."
        )
    }
