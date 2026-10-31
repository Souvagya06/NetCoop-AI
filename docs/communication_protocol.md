# Communication protocol

`AgentMessage` (see `backend/protocols/message_schema.py`):

| Field | Meaning |
|---|---|
| `incident_id`, `sender`, `timestamp` | identity |
| `message_type` | `finding`, `request_evidence`, `diagnosis`, `report`, `error` |
| `status` | `healthy` / `warning` / `critical` |
| `findings[]` | `code`, `description`, `severity`, `devices`, `device_scores`, `confidence` |
| `evidence` | supporting data (flagged devices, thresholds, detailed signals, failed links…) |
| `confidence` | **evidence score** 0-1, not a probability |
| `limitations` | what the agent could not verify |
| `request` | present only for `request_evidence`: `to`, `check`, `device_id`, `question` |

Telemetry contract: `TelemetrySnapshot` → `DeviceTelemetry` → `DeviceMetrics` (`telemetry_schema.py`). Unreachable devices carry probe-timeout values (latency 2000 ms, loss 100%) and `reachable=false`.
