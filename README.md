# NetCoop AI — Multi-Agent Network Fault Diagnosis & Interoperability

Five cooperating agents detect network problems, rank probable root causes and recommend actions.
Telemetry is **synthetic** (simulated campus network), so results demonstrate the method, not real-world accuracy.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                      # optional

python scripts/generate_dataset.py                        # data + trains both Isolation Forests
cd backend
pytest -q                                                 # 52 tests
python ml_models/evaluation/evaluate.py                   # held-out evaluation
uvicorn main:app --reload                                 # Web Dashboard & API at http://127.0.0.1:8000
# or directly: python main.py
```

Try one diagnosis without the server: `python scripts/run_diagnosis.py --scenario hardware_failure --seed 5`

## Architecture (hybrid orchestration)

```
telemetry ─► Orchestrator ─┬► Performance agent    ┐
                           ├► Infrastructure agent ├─ run in parallel, replies validated
                           └► Connectivity agent   ┘
                    ▲            │
                    │   Correlation agent ranks root causes; if the top two are close it asks
                    └── (via the orchestrator, max 2 rounds) one agent for a detailed breakdown
                                 ▼
                         Reporting agent ─► incident report
```
Agents never import each other; they only exchange `AgentMessage` objects (`backend/protocols/`).

## Main endpoints (prefix `/api`)
`GET /health` · `GET /scenarios` · `GET /topology` · `GET /agents` ·
`POST /telemetry/generate` · `POST /diagnosis/simulate {scenario, seed}` · `POST /diagnosis/run {snapshot}` ·
`GET /diagnosis/history` · `GET /diagnosis/{incident_id}`

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
