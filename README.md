# NetCoop AI — Multi-Agent Network Fault Diagnosis & Interoperability

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.2+-blue)](https://networkx.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Integrated-8E75B2?logo=google&logoColor=white)](https://ai.google.dev/)

An autonomous, cooperative **multi-agent network operations and fault diagnosis system** designed for campus and enterprise IT infrastructures. Five specialized, decoupled AI agents collaborate through strict message-passing protocols to monitor 20 interconnected network nodes, identify anomalies, rank probable root causes through inter-agent evidence exchanges, and generate actionable remediation reports with plain-language AI explanations.

---

## Key Highlights

- **Multi-Agent Interoperability**: 5 loosely-coupled agents (`Performance`, `Infrastructure`, `Connectivity`, `Correlation`, `Reporting`) that never import each other and communicate strictly via standardized `AgentMessage` protocols.
- **Hybrid Anomaly Detection**: Blends unsupervised machine learning (**Isolation Forests**) with deterministic heuristic domain rules (75% rules + 25% ML anomaly score).
- **Evidence-Weighted Correlation Engine**: Ranks root causes using mathematical corroboration and symptom-penalty logic, automatically triggering targeted inter-agent inquiry rounds when top hypotheses are contested.
- **Full-Stack Web Dashboard**: Built-in React SPA served directly by FastAPI featuring real-time device telemetry monitoring, interactive campus network topology graph, agent status trackers, and incident diagnosis reports.
- **11 Fault Scenarios**: Simulates campus-wide anomalies ranging from hardware failures, link cuts, and DNS outages to CPU overloads and packet loss.
- **Explainable & Safe**: Ground-truth isolation ensures agents diagnose blindly without cheating; outputs include advisory runbooks and optional Google Gemini executive summaries.

---

## Architecture & Agent Ecosystem

### Hybrid Orchestration Flow

```
                     ┌───────────────────────────────┐
                     │ Telemetry Snapshot (20 Nodes) │
                     └───────────────┬───────────────┘
                                     │ (Clean / Ground-Truth Stripped)
                                     ▼
                     ┌───────────────────────────────┐
                     │          Orchestrator         │
                     └───────────────┬───────────────┘
                                     │ Parallel Fan-Out
             ┌───────────────────────┼───────────────────────┐
             ▼                       ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
    │   Performance   │     │ Infrastructure  │     │  Connectivity   │
    │      Agent      │     │      Agent      │     │      Agent      │
    │ (IF + Rulesets) │     │ (IF + Rulesets) │     │(NetworkX Graph) │
    └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
             │                       │                       │
             └───────────────────────┼───────────────────────┘
                                     │ Fan-In & Protocol Validation
                                     ▼
                     ┌───────────────────────────────┐
                     │       Correlation Agent       │
                     │  (Hypothesis Scoring Engine)  │
                     └───────────────┬───────────────┘
                                     │ Contested Margin (< 0.10)?
                                     │ ──► Targeted Evidence Inquiry (Max 2 Rounds)
                                     ▼
                     ┌───────────────────────────────┐
                     │        Reporting Agent        │
                     │  (Remediation + Gemini AI)    │
                     └───────────────┬───────────────┘
                                     ▼
                     ┌───────────────────────────────┐
                     │  Incident Report & Advisory   │
                     └───────────────────────────────┘
```

### The 5 Cooperating Agents

| Agent | Domain & Function | Detection Mechanism |
|---|---|---|
| **Performance Agent** | Evaluates network traffic health: latency, jitter, packet loss, queue drops, and link congestion. | Heuristic threshold ramps + scikit-learn Isolation Forest model. |
| **Infrastructure Agent** | Monitors hardware health: CPU spikes, memory exhaustion, thermal stress, and interface error registers. | Domain rule ramps + scikit-learn Isolation Forest model. |
| **Connectivity Agent** | Inspects topology graphs, spanning tree paths, isolated node clusters, and core service reachability (DNS/DHCP). | `NetworkX` graph traversal (BFS / reachability) + protocol availability tests. |
| **Correlation Agent** | Synthesizes findings from analysis agents, penalizes symptoms when root causes exist, and queries peers for deep signals. | Evidence-weighted hypothesis ranking formula + 2-round bounded inquiry. |
| **Reporting Agent** | Compiles structured root-cause reports, prioritized remediation action steps, and plain-language summaries. | Rule-based recommendation engine + optional Google Gemini rephrasing. |

---

## How Diagnosis is Calculated

### 1. Hybrid Anomaly Confidence Formula
Each analysis agent blends expert heuristic rules with statistical anomaly scoring:
$$\text{Confidence} = (1 - \alpha) \cdot \text{Rule Confidence} + \alpha \cdot \text{ML Anomaly Score}$$
*(Default $\alpha = 0.25$, balancing 75% deterministic domain rules with 25% unsupervised Isolation Forest anomaly detection).*

### 2. Evidence-Weighted Correlation Formula
For each candidate root cause $H$, the Correlation Agent computes:
$$\text{Score}(H) = \text{Primary} \times \Big(\text{Base} + (1 - \text{Base}) \times \text{Corroboration}\Big) \times (1 - \text{Penalty})$$
- **$\text{Primary}$**: Confidence of the signature fault symptom (if absent, $\text{Score} = 0$).
- **$\text{Base}$**: Baseline credibility retained without external corroboration ($0.60$).
- **$\text{Corroboration}$**: Weighted peer support (e.g. latency spikes corroborate network congestion).
- **$\text{Penalty}$**: Dampens symptom hypotheses when deeper physical root causes are discovered (e.g. hardware failure penalizes pure congestion).

### 3. Dynamic Multi-Turn Tie-Breaks
If the margin between the top two hypotheses is below **$0.10$**, the Correlation Agent requests fine-grained evidence from the agent owning the discriminating signals (e.g. queue drop rates or interface errors), applying a $\pm 0.15 \times \text{signal strength}$ tiebreak adjustment to achieve decisive diagnosis.

---

## Campus Topology & Fault Scenarios

### Monitored Topology (20 Nodes)
- **3 Routers**: Core Campus Router (`RTR_CAMPUS_01`), Distribution Routers (`RTR_CAMPUS_02`, `RTR_CAMPUS_03`).
- **6 Access Switches**: `SW_CAMPUS_01` through `SW_CAMPUS_06`.
- **8 Wireless Access Points**: `AP_CAMPUS_01` through `AP_CAMPUS_08`.
- **3 Enterprise Servers**: DNS Server (`SRV_DNS_01`), DHCP Server (`SRV_DHCP_01`), Application Server (`SRV_APP_01`).

### Supported Fault Scenarios

| Scenario | Primary Root Cause | Observable Symptoms Across Network |
|---|---|---|
| `normal` | Baseline Operation | Healthy telemetry with benign statistical fluctuations. |
| `hardware_failure` | Internal Device Breakdown | High CPU + memory pressure + severe interface error bursts. |
| `link_failure` | Fiber / Cable Severance | Complete unreachability of downstream subtrees; NetworkX graph partition. |
| `network_congestion` | Saturated Trunk Link | Link utilization $> 80\%$, exponential queue drops, elevated latency. |
| `cpu_overload` | Process Spike / Denial-of-Service | CPU utilization $> 85\%$, process queue delays, mild latency jitter. |
| `memory_overload` | Memory Leak / Buffer Exhaustion | Memory utilization $> 85\%$, buffer allocation failures. |
| `interface_failure` | Port / Transceiver Malfunction | High packet loss with abnormal interface drop counts. |
| `latency_spike` | Route Flapping / Upstream Delay | Abnormal latency and jitter without local hardware degradation. |
| `packet_loss` | Intermittent Physical Degradation | Packet loss $> 1.5\%$ across transit hops. |
| `dns_failure` | Name Resolution Outage | DNS resolution success drops below $70\%$ across clients. |
| `dhcp_failure` | IP Allocation Pool Exhaustion | DHCP negotiation failure rates spike; clients fail to acquire leases. |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (only if rebuilding frontend; pre-built assets are included)

### 1. Setup Virtual Environment & Dependencies

```bash
# Clone repository
git clone https://github.com/Souvagya06/NetCoop-AI.git
cd NetCoop-AI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
cp .env.example .env    # optional: configure GEMINI_API_KEY
```

### 2. Run the Web Dashboard & API

You can start the backend and built-in frontend using any of the following:

**Windows 1-Click Script (PowerShell):**
```powershell
.\run_backend.ps1
```

**Windows 1-Click Script (CMD / Explorer):**
```cmd
run_backend.bat
```

**Direct Python Command:**
```bash
python backend/main.py
```

Open your browser:
- **Interactive Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **API Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## Testing & CLI Diagnosis

### Run Automated Tests (52 Tests)
```bash
pytest backend/tests
```

### Run Standalone CLI Diagnosis
Execute an end-to-end multi-agent diagnosis directly in your terminal:
```bash
python scripts/run_diagnosis.py --scenario hardware_failure --seed 5
```

### Re-Generate Synthetic Datasets & Retrain ML Models
```bash
python scripts/generate_dataset.py
python backend/ml_models/evaluation/evaluate.py
```

---

## REST API Reference

All API routes are prefixed with `/api`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status. |
| `GET` | `/api/topology` | Full network topology graph structure and node metadata. |
| `GET` | `/api/agents` | Registered agents, capabilities, and operational status. |
| `GET` | `/api/scenarios` | List of all 11 simulated fault scenarios. |
| `GET` | `/api/telemetry/live` | Current monitored telemetry across all 20 devices. |
| `POST` | `/api/telemetry/generate` | Generate synthetic snapshot with simulation ground truth. |
| `POST` | `/api/diagnosis/simulate` | Trigger simulation for a scenario and run full agent diagnosis. |
| `POST` | `/api/diagnosis/run` | Run multi-agent diagnosis on an externally provided telemetry snapshot. |
| `GET` | `/api/diagnosis/history` | Historical incident log with severity and root cause labels. |
| `GET` | `/api/diagnosis/{id}` | Detailed incident report including step-by-step agent timeline. |

---

## Project Structure

```
NetCoop-AI/
├── backend/
│   ├── agents/                     # The 5 specialized AI agents
│   │   ├── base_agent.py           # Abstract base class & finding aggregator
│   │   ├── connectivity_agent/     # Topology graph & service health
│   │   ├── correlation_agent/      # Hypothesis scoring & tie-break engine
│   │   ├── infrastructure_agent/   # CPU, memory, & hardware health
│   │   ├── performance_agent/      # Latency, loss, & congestion analysis
│   │   └── reporting_agent/        # Advisory runbooks & Gemini integration
│   ├── api/                        # FastAPI route handlers
│   ├── data_generator/             # Synthetic telemetry simulation & scenarios
│   ├── ml_models/                  # Isolation Forest anomaly detectors & evaluation
│   ├── orchestrator/               # Hybrid fan-out/fan-in & registry
│   ├── protocols/                  # AgentMessage & Telemetry Pydantic schemas
│   ├── services/                   # Diagnosis and dataset service layer
│   ├── tests/                      # Pytest test suite (52 tests)
│   ├── config.py                   # Central configuration & environment variables
│   └── main.py                     # Application entry point & SPA static server
├── frontend/                       # React 19 + Vite + Tailwind dashboard
│   ├── src/                        # Dashboard components, topology viewer, API client
│   └── dist/                       # Production pre-built assets
├── scripts/                        # Dataset generation & CLI diagnosis runners
├── docs/                           # Architecture, protocols, and workflow docs
├── run_backend.ps1                 # Windows 1-click startup script (PowerShell)
├── run_backend.bat                 # Windows 1-click startup script (CMD)
└── requirements.txt                # Python project dependencies
```

---

## Design Principles & Honesty Controls

The local API allows the frontend origins `localhost` and `127.0.0.1` on ports
3000 and 5173. Set `CORS_ORIGINS` in `.env` to a comma-separated list of exact
origins when the frontend runs elsewhere. Request validation errors return a
422 response with a string `detail`, a machine-readable `code`, and sanitized
field errors (submitted values are not echoed).

## Honest limitations
- Evidence scores are heuristic rankings, not calibrated probabilities.
- Thresholds/rules are hand-chosen; mild faults can fall below them and be reported as "normal".
- Diagnosis uses one snapshot (no time series). Incident history is in-memory.
- Synthetic data comes from our own assumptions; accuracy on real networks would differ.
