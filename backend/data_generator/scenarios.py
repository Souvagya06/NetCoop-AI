"""The 11 fault scenarios. Each fault interpolates between a 'mild' and a 'severe'
value per metric, so mild faults overlap with each other and with normal noise."""
from __future__ import annotations

SCENARIOS = [
    "normal",
    "latency_spike",
    "packet_loss",
    "network_congestion",
    "cpu_overload",
    "memory_overload",
    "hardware_failure",
    "interface_failure",
    "link_failure",
    "dns_failure",
    "dhcp_failure",
]

SCENARIO_INFO = {
    "normal": ("Normal operation", "Everything works properly"),
    "latency_spike": ("Latency spike", "Network response becomes unusually slow"),
    "packet_loss": ("Packet loss", "Some transmitted packets fail to reach their destination"),
    "network_congestion": ("Network congestion", "Traffic exceeds available capacity"),
    "cpu_overload": ("CPU overload", "A network device experiences excessive CPU usage"),
    "memory_overload": ("Memory overload", "A device experiences unusually high memory usage"),
    "hardware_failure": ("Hardware failure", "A device develops severe operational problems"),
    "interface_failure": ("Interface failure", "A physical/logical interface stops working properly"),
    "link_failure": ("Link failure", "Communication between two devices is interrupted"),
    "dns_failure": ("DNS failure", "Domain names cannot be resolved correctly"),
    "dhcp_failure": ("DHCP failure", "Devices cannot obtain valid network configuration"),
}

# metric -> (value at severity 0, value at severity 1)
FAULT_PROFILES = {
    "latency_spike": {"latency_ms": (80, 600), "jitter_ms": (10, 90), "packet_loss_pct": (0.3, 3.0)},
    "packet_loss": {"packet_loss_pct": (1.5, 15), "latency_ms": (30, 150), "jitter_ms": (5, 40)},
    "network_congestion": {
        "link_utilization_pct": (75, 99), "queue_drops": (150, 6000), "latency_ms": (60, 400),
        "jitter_ms": (10, 70), "packet_loss_pct": (1, 10), "cpu_utilization_pct": (40, 75),
    },
    "cpu_overload": {
        "cpu_utilization_pct": (80, 99.5), "queue_drops": (50, 3000), "latency_ms": (40, 400),
        "packet_loss_pct": (0.5, 8), "memory_utilization_pct": (55, 85), "link_utilization_pct": (45, 85),
    },
    "memory_overload": {
        "memory_utilization_pct": (85, 99), "cpu_utilization_pct": (45, 85),
        "latency_ms": (30, 200), "packet_loss_pct": (0.2, 4),
    },
    "hardware_failure": {
        "cpu_utilization_pct": (85, 100), "memory_utilization_pct": (80, 99), "packet_loss_pct": (8, 40),
        "latency_ms": (150, 900), "queue_drops": (1500, 10000), "interface_errors": (40, 400), "jitter_ms": (30, 120),
    },
    "interface_failure": {
        "interface_errors": (80, 800), "packet_loss_pct": (3, 30), "link_utilization_pct": (25, 5), "latency_ms": (30, 200),
    },
}

# device types that can be the root of each device-level fault
TARGET_TYPES = {
    "latency_spike": ["router", "switch", "access_point"],
    "packet_loss": ["router", "switch", "access_point"],
    "network_congestion": ["router", "switch"],
    "cpu_overload": ["router", "switch", "server"],
    "memory_overload": ["router", "switch", "server"],
    "hardware_failure": ["router", "switch"],
    "interface_failure": ["router", "switch", "access_point"],
}

# how strongly a device-level fault degrades the devices behind it (0 = not at all)
PROPAGATION = {
    "latency_spike": 0.8,
    "packet_loss": 0.3,
    "network_congestion": 1.0,
    "cpu_overload": 0.8,
    "memory_overload": 0.3,
    "hardware_failure": 1.0,
    "interface_failure": 0.3,
}
