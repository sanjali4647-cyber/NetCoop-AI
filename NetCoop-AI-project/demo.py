"""Offline, explicitly synthetic demonstration. Does not modify netcoop.db."""
import argparse
import json

from server import diagnostic_report, task_result, validate_report
from demo_scenarios import make_rows


def main():
    parser = argparse.ArgumentParser(description="Run an offline synthetic NetCoop diagnosis")
    parser.add_argument("scenario", choices=["normal", "link_congestion", "weak_wifi", "interface_fault", "dns_failure", "dhcp_failure", "server_downtime", "database_failure", "connection_pool_exhaustion", "missing"])
    args = parser.parse_args()
    rows = make_rows(args.scenario)
    result, events = task_result(f"Synthetic demo: {args.scenario}", samples=rows)
    report = diagnostic_report(f"DEMO-{args.scenario.upper()}", result)
    validate_report(report)
    print(json.dumps({"demo_data": "SYNTHETIC - NOT LIVE NETWORK DATA", "scenario": args.scenario, "agent_trace": result.get("message_log", []), "report": report}, indent=2))


if __name__ == "__main__":
    main()
