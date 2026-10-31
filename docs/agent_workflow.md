# Agent workflow

1. **Fan-out:** orchestrator sends the same snapshot (without ground truth) to Performance, Infrastructure and Connectivity in parallel (timeout per agent).
2. **Fan-in:** every reply is validated (`protocols/validator.py`). A crashed/slow agent becomes an `error` message and a limitation; the diagnosis continues.
3. **Correlation:** per-hypothesis score = `primary_conf × (base + (1-base)×corroboration) × (1 − penalty)`. Symptom hypotheses (latency, loss, congestion) are penalised when a deeper cause (device overload, hardware, link) is present. If the top hypotheses are within 0.10, the agent emits `request_evidence`; the orchestrator routes it to the agent owning the discriminating signals (max 2 rounds). The reply's `detailed_signals` nudge the contested scores (±0.15).
4. **Incident threshold:** top score below 0.45 → "normal / minor noise".
5. **Reporting:** root cause, key metrics, evidence list, alternatives, rule-based actions; optional Gemini rewrite (needs `GEMINI_API_KEY`; never invents facts by prompt, but is untested here).

Finding codes: performance `latency_spike, packet_loss, network_congestion`; infrastructure `device_overload, memory_pressure, hardware_failure, interface_failure`; connectivity `link_failure, dns_failure, dhcp_failure, downstream_degradation`.
