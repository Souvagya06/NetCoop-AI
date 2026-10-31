"""Rule-based, advisory recommendations. They always require administrator verification."""
from __future__ import annotations

from typing import List

RECOMMENDATIONS = {
    "network_congestion": [
        "Identify top talkers/applications on {device} and look for abnormal traffic spikes.",
        "Review bandwidth allocation, QoS policies and rate limits on the affected uplinks.",
        "Check whether the uplink capacity of {device} is still adequate; consider link aggregation.",
        "Look for broadcast storms or loops if utilisation is unexpectedly high.",
        "Re-measure utilisation and queue drops after the change.",
    ],
    "latency_spike": [
        "Trace the path from the affected clients to {device} to locate where delay is introduced.",
        "Check for transient congestion or a misbehaving client generating bursts.",
        "Review routing changes or failovers around the time the latency started.",
        "Monitor jitter-sensitive services (VoIP/video) until latency recovers.",
    ],
    "packet_loss": [
        "Inspect the physical layer on {device}: cables, transceivers, duplex/speed settings.",
        "Check interface error counters and queue drops on both ends of the affected links.",
        "Test with a different cable/port to isolate a faulty component.",
        "Re-run a packet-loss test after each change to confirm improvement.",
    ],
    "cpu_overload": [
        "Inspect CPU-intensive processes on {device} (control-plane load, routing updates, logging).",
        "Identify abnormal traffic spikes or scanning activity hitting the device's control plane.",
        "Review bandwidth allocation, QoS and control-plane policing settings.",
        "Check device capacity and hardware health; plan an upgrade if load is sustained.",
        "Monitor network performance after intervention.",
    ],
    "memory_overload": [
        "Check memory usage by process on {device} and look for leaks (compare with uptime).",
        "Review routing/ARP/MAC table sizes for unexpected growth.",
        "Schedule a controlled restart or firmware update if a leak is confirmed.",
        "Verify logging/monitoring features are not consuming excess memory.",
    ],
    "hardware_failure": [
        "Check {device} hardware health: fans, power supplies, temperature and line cards.",
        "Review device logs for hardware faults, crashes or error bursts.",
        "Prepare a failover or replacement for {device}; reroute critical traffic if possible.",
        "Open a vendor support case with the collected evidence.",
        "Verify downstream devices recover once traffic is moved off {device}.",
    ],
    "interface_failure": [
        "Check the affected interface(s) on {device}: status, CRC/FCS errors, flapping.",
        "Replace or re-seat the cable/transceiver and test the port.",
        "Verify speed/duplex negotiation matches the peer device.",
        "Move traffic to a spare port while troubleshooting.",
    ],
    "link_failure": [
        "Verify the physical link {link}: cable, transceiver, patch panel and port LEDs.",
        "Check whether the upstream interface is administratively or operationally down.",
        "Bring up a redundant path if one exists, or relocate critical devices temporarily.",
        "Confirm all downstream devices become reachable after restoration.",
    ],
    "dns_failure": [
        "Check that the DNS service on {device} is running and answering queries.",
        "Test resolution against a secondary/public resolver to confirm the scope.",
        "Review DNS server logs, forwarders and recent configuration changes.",
        "Ensure clients have a working secondary DNS server configured.",
    ],
    "dhcp_failure": [
        "Check that the DHCP service on {device} is running and has free leases in the scope.",
        "Verify DHCP relay/helper settings on the affected switches and access points.",
        "Review DHCP server logs for NAKs or exhausted pools.",
        "Renew leases on a test client after the fix.",
    ],
}

NO_INCIDENT = ["No corrective action required. Continue routine monitoring."]
UNDETERMINED = ["Restore the failed analysis agents and re-run the diagnosis.", "Inspect the network manually in the meantime."]


def recommend(cause: str, device: str | None, link: List[str] | None) -> List[str]:
    if cause == "normal":
        return NO_INCIDENT
    if cause == "undetermined":
        return UNDETERMINED
    link_txt = f"{link[0]} <-> {link[1]}" if link else "the affected uplink"
    return [t.format(device=device or "the affected device", link=link_txt) for t in RECOMMENDATIONS.get(cause, [])]
