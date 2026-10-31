# NetCoop AI dashboard

The React dashboard uses the FastAPI service in `../backend` for campus topology,
agent details, diagnosis simulations, and incident history.

## Run locally

Start the backend from the `backend/` directory:

```bash
uvicorn main:app --reload
```

Then start the frontend from this directory:

```bash
npm install
npm run dev
```

Open the Vite URL shown in the terminal (usually `http://localhost:5173`).
The dashboard calls `http://127.0.0.1:8000/api` by default. Set
`VITE_API_BASE_URL` to change the API base URL.

## Dashboard features

- Run a diagnosis against any backend-provided simulation scenario and seed.
- Review the suspected cause, evidence score, affected devices, evidence, and
  advisory recommendations.
- Inspect analysis-agent findings and the orchestration timeline.
- Explore the campus topology and recent incident history.
- Export the selected incident report as JSON.

The backend uses synthetic telemetry for demonstrations. Diagnosis scores are
evidence rankings, not calibrated probabilities; recommendations require
administrator verification.
