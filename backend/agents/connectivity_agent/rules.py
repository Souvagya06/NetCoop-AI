from __future__ import annotations

DNS_FAIL_BELOW = 85.0          # a device's DNS success rate below this counts as failing
DHCP_FAIL_BELOW = 85.0
SERVICE_MIN_FRACTION = 0.5     # share of relevant devices that must be failing

# a reachable device counts as "degraded" if any of these hold
DEGRADED_LATENCY_MS = 45.0
DEGRADED_LOSS_PCT = 0.8
DEGRADED_JITTER_MS = 15.0
DOWNSTREAM_MIN_DEVICES = 2
DOWNSTREAM_MIN_FRACTION = 0.6

DESCRIPTIONS = {
    "link_failure": "{n} device(s) unreachable behind a failed link/uplink.",
    "dns_failure": "DNS resolution failing on {n} device(s).",
    "dhcp_failure": "DHCP lease acquisition failing on {n} device(s).",
    "downstream_degradation": "Devices downstream of {device} are degraded while it remains reachable.",
}
