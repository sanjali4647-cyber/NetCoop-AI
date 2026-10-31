"""Opt-in, deterministic synthetic inputs for tests and the labeled demo page only."""
from datetime import datetime, timedelta, timezone


def make_rows(scenario):
    if scenario == "missing":
        return []
    specs = {
        "normal": {"link_utilization_pct": ("percent", [40, 41], 40), "latency_ms": ("ms", [20, 21], 20)},
        "link_congestion": {"link_utilization_pct": ("percent", [40, 41], 96), "queue_drops": ("count", [1, 2], 150), "latency_ms": ("ms", [20, 21], 180)},
        "weak_wifi": {"rssi_dbm": ("dBm", [-47, -49], -90), "retransmission_pct": ("percent", [2, 3], 88)},
        "interface_fault": {"interface_errors": ("count", [1, 2], 100), "packet_loss_pct": ("percent", [0.1, 0.2], 12), "link_utilization_pct": ("percent", [40, 41], 40)},
        "dns_failure": {"dns_status": ("state", ["ok"], "failed")},
        "dhcp_failure": {"dhcp_status": ("state", ["ok"], "failed")},
        "server_downtime": {"server_status": ("state", ["up"], "down")},
        "database_failure": {"database_status": ("state", ["ok"], "failed")},
        "connection_pool_exhaustion": {"connection_pool_usage_pct": ("percent", [70, 72], 98)},
        "agents_disagree": {"link_utilization_pct": ("percent", [40, 41], 96), "latency_ms": ("ms", [20, 21], 150), "cpu_pct": ("percent", [30, 31], 97)},
    }
    if scenario not in specs:
        raise ValueError(f"Unknown scenario: {scenario}")
    rows = []
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    device = "SYNTHETIC_TEST_DEVICE"
    for metric, (unit, baseline, fault) in specs[scenario].items():
        for i in range(20):
            rows.append({"timestamp": (start + timedelta(minutes=i)).isoformat().replace("+00:00", "Z"), "device_id": device, "metric": metric, "value": baseline[i % len(baseline)], "unit": unit, "source": "SYNTHETIC TEST FIXTURE ONLY", "parent_device_id": None, "path_id": "SYNTHETIC-TEST-PATH"})
        rows.append({"timestamp": (start + timedelta(minutes=20)).isoformat().replace("+00:00", "Z"), "device_id": device, "metric": metric, "value": fault, "unit": unit, "source": "SYNTHETIC TEST FIXTURE ONLY", "parent_device_id": None, "path_id": "SYNTHETIC-TEST-PATH"})
    return rows
