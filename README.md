# NetCoop AI — Multi-Agent Network Fault Diagnosis & Interoperability

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.2+-blue)](https://networkx.org/)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel&logoColor=white)](https://net-coop-ai-quantum-coders.vercel.app/)
[![Render](https://img.shields.io/badge/Backend-Render-46E3B7?logo=render&logoColor=white)](https://netcoop-ai-d02h.onrender.com)

An autonomous, cooperative **multi-agent network operations and fault diagnosis platform** designed for campus and enterprise IT infrastructures (developed for the **IIT Bhubaneswar Agentic AI Grand Finale Challenge**). Five decoupled, specialized AI agents collaborate through standardized protocols to monitor 20 network nodes, detect physical and logical anomalies, rank probable root causes through inter-agent evidence exchanges, and generate actionable remediation runbooks.

---

## 👥 Team: Quantum Coders

| Member Name | GitHub Profile | Role |
| :--- | :--- | :--- |
| **Souvagya Karmakar** | [@Souvagya06](https://github.com/Souvagya06) | Team Lead & Full-Stack System Architecture |
| **Sushmita Roy** | [@2006sushmita](https://github.com/2006sushmita) | Multi-Agent Coordination & Protocol Design |
| **Bikram Pal** | [@Bikram-pal](https://github.com/Bikram-pal) | ML Anomaly Models & Telemetry Analytics |
| **Anirban Pal** | [@Alex05606](https://github.com/Alex05606) | Frontend Interactive Dashboard & Visualization |

---

## 🌐 Live Deployments

- **Live Web Dashboard (Vercel):** [https://net-coop-ai-quantum-coders.vercel.app/](https://net-coop-ai-quantum-coders.vercel.app/)
- **Backend API & Swagger Docs (Render):** [https://netcoop-ai-d02h.onrender.com/docs](https://netcoop-ai-d02h.onrender.com/docs)
- **API Health Endpoint (Render):** [https://netcoop-ai-d02h.onrender.com/api/health](https://netcoop-ai-d02h.onrender.com/api/health)

---

## 🚀 Key Highlights & Capabilities

- **Decoupled 5-Agent Architecture**: Five specialized agents (`Performance`, `Infrastructure`, `Connectivity`, `Correlation`, and `Reporting`) that strictly exchange strongly-typed Pydantic [`AgentMessage`](backend/protocols/message_schema.py) contracts with zero code coupling.
- **Hybrid Anomaly Detection**: Blends unsupervised machine learning (**Isolation Forests**) with deterministic heuristic domain rules (75% domain rules + 25% ML anomaly score).
- **Time-Window Rolling Buffer**: Maintains a thread-safe sliding history (last 10 readings per device) tracking **metric trend slope**, **rate of change**, and **fault persistence** to eliminate transient spike misclassifications.
- **Evidence-Weighted Correlation Engine**: Ranks root causes using mathematical corroboration and symptom-penalty logic, automatically triggering targeted inter-agent inquiry rounds when top hypotheses are contested.
- **Interactive Web Dashboard**: React 18 SPA featuring an interactive SVG campus topology map, live per-device metrics inspector, dedicated popup diagnostics windows for each agent, and real-time polling.
- **11 Simulated Fault Scenarios**: Comprehensive test coverage across hardware breakdowns, fiber cuts, link congestion, CPU/memory overloads, DNS outages, and DHCP failures across 20 devices.
- **Explainable & Safe**: Zero data leakage (ground truth is stripped before agent ingestion); outputs include step-by-step remediation procedures and optional Google Gemini executive summaries.

---

## 🏗️ Architecture & Hybrid Orchestration Flow

```
                      ┌─────────────────────────────────────────┐
                      │    Network Telemetry Ingestion Source   │
                      │   (20 Campus Nodes · Raw Metrics)       │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │    Ground-Truth Stripping & Validator   │
                      │   (Clean snapshot: zero data leakage)   │
                      └────────────────────┬────────────────────┘
                                           │
               ┌───────────────────────────┴───────────────────────────┐
               │              CENTRAL HYBRID ORCHESTRATOR              │
               └───────┬───────────────────┬───────────────────┬───────┘
                       │ (Parallel Fan-Out)│                   │
                       ▼                   ▼                   ▼
             ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
             │Performance Agent │ │Infrastructure Ag │ │Connectivity Agent│
             │Latency, Jitter,  │ │CPU, Memory,      │ │Graph Topology,   │
             │Loss, Queue Drops │ │Errors, Overload  │ │Root vs Affected  │
             │(Rules + IsoForest│ │(Rules + IsoForest│ │(NetworkX Tree)   │
             └─────────┬────────┘ └────────┬─────────┘ └────────┬─────────┘
                       │                   │                    │
                       └───────────────┬───┴────────────────────┘
                                       │ Fan-In (Validated AgentMessages)
                                       ▼
                       ┌───────────────────────────────┐
                       │    Fault Correlation Agent    │
                       │ • Scores 10 fault hypotheses  │
                       │ • Resolves close contests via │
                       │   targeted Evidence Requests  │
                       │ • Attributes root device/link │
                       └───────────────┬───────────────┘
                                       │ Ranked Diagnosis
                                       ▼
                       ┌───────────────────────────────┐
                       │        Reporting Agent        │
                       │ • Generates standard JSON     │
                       │ • Preserves uncertainty & lims│
                       │ • Remediation actions engine  │
                       │ • Optional Gemini LLM summary │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │      Interactive Output       │
                       │ • Web Dashboard (Vercel)      │
                       │ • OpenAPI JSON (Render)       │
                       └───────────────────────────────┘
```

---

## 🤖 The 5 Cooperating AI Agents

| Agent | Domain & Responsibility | Detection & Reasoning Mechanism |
|---|---|---|
| **Performance Agent** | Evaluates traffic health: latency, jitter, packet loss, queue drops, and link congestion. | Heuristic threshold ramps ($\ge 80\%$ link util) + Scikit-learn Isolation Forest model. |
| **Infrastructure Agent** | Monitors hardware health: CPU spikes, memory exhaustion, thermal stress, and interface error registers. | Domain rule ramps ($\ge 80\%$ CPU/mem) + Scikit-learn Isolation Forest model. |
| **Connectivity Agent** | Inspects topology graphs, spanning tree paths, isolated node clusters, and core service reachability (DNS/DHCP). | `NetworkX` graph traversal (BFS / reachability) + protocol availability tests. |
| **Correlation Agent** | Synthesizes findings from analysis agents, penalizes symptoms when root causes exist, and queries peers for deep signals. | Evidence-weighted hypothesis ranking formula + 2-round bounded inquiry. |
| **Reporting Agent** | Compiles structured root-cause reports, prioritized remediation action steps, and plain-language summaries. | Deterministic recommendation engine + optional Google Gemini rephrasing. |

---

## 📐 How Diagnosis is Calculated

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
If the margin between the top two hypotheses is below **$0.10$**, the Correlation Agent requests fine-grained evidence from the agent owning the discriminating signals (e.g. queue drop rates or interface errors), applying a $\pm 0.15 \times \text{signal strength}$ tiebreak adjustment to achieve a decisive diagnosis.

---

## 🏫 Campus Topology & Supported Scenarios

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
| `network_congestion` | Saturated Trunk Link | Link utilization $\ge 80\%$, exponential queue drops, elevated latency. |
| `cpu_overload` | Process Spike / DoS | CPU utilization $\ge 80\%$, process queue delays, mild latency jitter. |
| `memory_overload` | Memory Leak / Buffer Exhaustion | Memory utilization $\ge 80\%$, buffer allocation failures. |
| `interface_failure` | Port / Transceiver Malfunction | High packet loss with abnormal interface drop counts. |
| `latency_spike` | Route Flapping / Upstream Delay | Abnormal latency and jitter without local hardware degradation. |
| `packet_loss` | Intermittent Physical Degradation | Packet loss $\ge 1.0\%$ across transit hops. |
| `dns_failure` | Name Resolution Outage | DNS resolution success drops below $95\%$ across clients. |
| `dhcp_failure` | IP Pool Exhaustion | DHCP negotiation failure rates spike; clients fail to acquire leases. |

---

## 💻 Local Setup & Quick Start

### 1. Clone & Set Up Python Virtual Environment
```bash
git clone https://github.com/Souvagya06/NetCoop-AI.git
cd NetCoop-AI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
cp .env.example .env    # optional: configure GEMINI_API_KEY
```

### 2. Run the Full Application (Backend + Frontend)
```bash
python backend/main.py
```
Open your browser:
- **Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **API Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 🧪 Testing & Evaluation

### Run Automated Tests (52 Passing Tests)
```bash
pytest backend/tests -v
```

### Run Standalone CLI Diagnosis
```bash
python scripts/run_diagnosis.py --scenario hardware_failure --seed 42
```

### Run Baseline & Calibration Evaluation
```bash
python backend/ml_models/evaluation/evaluate.py
python backend/ml_models/evaluation/calibration.py
```

---

## 📡 REST API Reference

All API routes are prefixed with `/api`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status. |
| `GET` | `/api/topology` | Full network topology graph structure and node metadata. |
| `GET` | `/api/agents` | Registered agents, capabilities, and operational status. |
| `GET` | `/api/scenarios` | List of all 11 simulated fault scenarios. |
| `GET` | `/api/telemetry/live` | Current monitored telemetry across all 20 devices. |
| `GET` | `/api/telemetry/buffer` | Rolling-window trends (slope, rate of change, persistence). |
| `POST` | `/api/telemetry/push` | External telemetry ingestion endpoint. |
| `POST` | `/api/telemetry/generate` | Generate synthetic snapshot with simulation ground truth. |
| `POST` | `/api/diagnosis/simulate` | Trigger simulation for a scenario and run full agent diagnosis. |
| `POST` | `/api/diagnosis/run` | Run multi-agent diagnosis on an externally provided telemetry snapshot. |
| `GET` | `/api/diagnosis/history` | Historical incident log with severity and root cause labels. |
| `GET` | `/api/diagnosis/{id}` | Detailed incident report including step-by-step agent timeline. |

---

## ⚖️ Honest Limitations & Design Principles

- **Evidence Scores vs Probabilities**: Confidence values are heuristic ranking scores in $[0, 1]$, not calibrated Bayesian probabilities.
- **Synthetic Telemetry**: The data is generated from simulated campus network topologies to demonstrate multi-agent diagnosis and interoperability without accessing production physical campus infrastructure.
- **Advisory Recommendations**: All recommended actions are advisory runbooks intended for network administrator review; no automated destructive remediation is performed without human confirmation.

---

### 📄 License & Attribution
Developed for the **IIT Bhubaneswar Agentic AI Grand Finale Hackathon** by **Team Quantum Coders**.
