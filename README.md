# OpsPilot AI
### Evidence-Driven Autonomous Incident Investigation and Recovery Platform

OpsPilot AI is a backend-based incident investigation and recovery platform designed to detect simulated system failures, collect evidence, identify possible root causes, recommend recovery actions, and verify whether recovery was successful.

It includes a human-in-the-loop approval mechanism to prevent recovery actions from being executed without authorization.

---

## 1. Problem Statement

Software systems can experience incidents such as database outages, API degradation, memory exhaustion, and deployment failures.

Identifying the root cause manually can take time, especially when engineers need to analyze multiple logs and system metrics.

OpsPilot AI addresses this problem by providing a structured incident investigation workflow that:

- Detects simulated incidents.
- Collects system evidence.
- Classifies application logs.
- Identifies suspected root causes.
- Generates recovery plans.
- Requires human approval before execution.
- Executes recovery in a controlled simulator.
- Independently verifies recovery results.
- Maintains an audit history of important actions.

## 2. Key Features

### Incident Detection
Detects incidents using simulated application logs and system evidence.

### Evidence Collection
Collects system information such as:
- Database status
- API status
- Error rate
- P95 response time
- CPU usage
- Memory usage
- Active database connections

### Root Cause Analysis
Uses a rule-based scoring engine to identify suspected incident causes and provide supporting evidence.

### Incident Orchestration
Coordinates fault injection, log classification, evidence analysis, diagnosis, and recovery planning.

### Human-in-the-Loop Approval
Recovery plans require explicit human approval before execution.

### Automated Recovery Simulation
Supports simulated recovery actions for:
- Database connectivity failures
- API performance degradation
- Resource exhaustion
- Deployment regression

### Independent Recovery Verification
Checks the resulting simulated system state against expected recovery conditions.

### Audit History
Stores incident-related actions, including recovery planning, approval, execution, and verification events.

### Evaluation Engine
Evaluates diagnosis results against the simulator's known ground truth.

## 3. System Architecture

```text
                  OpsPilot AI
                       |
                       v
              Fault Simulator
                       |
                       v
              Incident Orchestrator
                       |
             +---------+---------+
             |                   |
             v                   v
        Log Classifier      Evidence Engine
             |                   |
             +---------+---------+
                       |
                       v
                RCA Engine
                       |
                       v
               Recovery Planner
                       |
                       v
              Human Approval
                       |
                       v
              Recovery Engine
                       |
                       v
             Recovery Verification
                       |
                       v
                Audit History
                       |
                       v
                 SQLite DB
```

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| FastAPI | REST API development |
| SQLite | Persistent data storage |
| Uvicorn | ASGI server |
| Pytest | Automated testing |
| Python-dotenv | Environment configuration |
| Swagger UI | API testing and documentation |

## 5. Simulated Incident Scenarios

OpsPilot AI currently supports five predefined scenarios.

| Scenario | Expected Root Cause |
|---|---|
| database_outage | DATABASE_CONNECTIVITY_FAILURE |
| api_degradation | API_PERFORMANCE_DEGRADATION |
| memory_exhaustion | RESOURCE_EXHAUSTION |
| deployment_regression | DEPLOYMENT_REGRESSION |
| healthy_system | NO_INCIDENT |

The simulator provides known ground truth, allowing diagnosis predictions to be evaluated.

## 6. API Endpoints

### General APIs

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check application health |
| GET | `/scenarios` | List available scenarios |
| GET | `/collect-evidence` | Collect simulated system evidence |
| GET | `/classify-logs` | Classify application logs |
| GET | `/analyze-logs` | Analyze application logs |
| GET | `/evaluate` | Evaluate diagnosis performance |
| GET | `/recovery/{incident_id}` | Retrieve recovery plan |

### Incident APIs

| Method | Endpoint | Description |
|---|---|---|
| POST | `/simulate/{scenario_id}` | Inject a simulated fault |
| POST | `/investigate` | Investigate an incident |
| POST | `/workflow/{scenario_id}` | Execute the incident workflow |

### Recovery APIs

| Method | Endpoint | Description |
|---|---|---|
| POST | `/recovery/plan/{scenario_id}` | Generate a recovery plan |
| POST | `/recovery/{incident_id}/approve` | Approve recovery |
| POST | `/recovery/{incident_id}/reject` | Reject recovery |
| POST | `/recovery/{incident_id}/execute` | Execute approved recovery |

### Audit API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/audit/{incident_id}` | Retrieve incident audit history |

## 7. Project Structure

```text
opspilot-ai/
│
├── main.py
├── fault_simulator.py
├── evidence_engine.py
├── rca_engine.py
├── recovery_engine.py
├── incident_orchestrator.py
├── evaluation_engine.py
├── database.py
│
├── test_diagnosis.py
├── test_evaluation.py
├── test_recovery.py
├── test_recovery_verification.py
├── test_simulator.py
├── test_recovery_api.py
│
├── requirements.txt
├── README.md
├── opspilot.db
│
└── .venv/
```

## 8. Installation and Setup

### Prerequisites

- Python 3.10 or higher
- pip
- VS Code (recommended)

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd opspilot-ai
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Activate the environment

Windows:

```bash
.venv\Scripts\activate
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Start the application

```bash
uvicorn main:app --reload
```

### Step 6: Open Swagger UI

Visit:

http://127.0.0.1:8000/docs

You can explore and test the available API endpoints through Swagger UI.

## 9. Running Automated Tests

Run the complete test suite:

```bash
pytest -v
```

**Current test result: 42 tests passed.**

The tests cover diagnosis, fault simulation, recovery planning, approval controls, recovery execution, verification, and API behavior.

## 10. Evaluation Results

The current evaluation engine was tested against five predefined simulated scenarios.

| Metric | Result |
|---|---:|
| Correct scenario predictions | 5/5 |
| Diagnosis accuracy | 100% |
| True positives | 4 |
| False positives | 0 |
| True negatives | 1 |
| False negatives | 0 |
| Precision | 100% |
| Recall | 100% |
| F1 Score | 100% |

**Important:** These results apply only to the five predefined simulator scenarios. They do not represent real-world production performance.

## 11. Safety and Limitations

- All incident scenarios and recovery operations are simulated.
- The platform does not monitor or modify real production infrastructure.
- Root cause analysis currently uses deterministic rule-based scoring.
- Recovery execution requires human approval.
- Recovery verification checks simulated system state.
- The current evaluation dataset is small and predefined.
- Audit history validation and concurrent execution testing remain areas for further verification.
- An LLM-based autonomous investigation agent is not yet integrated.

## 12. Future Enhancements

- Adaptive investigation strategies.
- Integration with LangGraph for agent orchestration.
- LLM-assisted root cause explanations.
- Integration with real monitoring platforms.
- React-based incident management dashboard.
- Prometheus and Grafana integration.
- More complex fault-injection scenarios.
- Advanced reliability and concurrency testing.

## 13. Project Objective

The objective of OpsPilot AI is to demonstrate how evidence-driven investigation, controlled recovery, human approval, and independent verification can be combined into a structured incident management system.

---

**Project:** OpsPilot AI  
**Category:** Backend Engineering / AI Engineering / Site Reliability Engineering  
**Status:** Simulated MVP  
**Primary Technologies:** Python, FastAPI, SQLite, Pytest