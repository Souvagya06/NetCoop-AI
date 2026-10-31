const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== "undefined" && window.location.port === "5173"
    ? "http://127.0.0.1:8000/api"
    : "/api")
).replace(/\/$/, "");

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error(`Can't reach the NetCoop API at ${API_BASE}. Start the FastAPI backend and try again.`);
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // The response body may not be JSON.
    }
    throw new Error(detail);
  }

  return response.json();
}

export const api = {
  health: () => request("/health"),
  scenarios: () => request("/scenarios"),
  topology: () => request("/topology"),
  agents: () => request("/agents"),
  history: () => request("/diagnosis/history"),
  liveTelemetry: () => request("/telemetry/live"),
  simulate: (scenario, seed) =>
    request("/diagnosis/simulate", {
      method: "POST",
      body: JSON.stringify({ scenario, seed }),
    }),
  incident: (id) => request(`/diagnosis/${encodeURIComponent(id)}`),
};
