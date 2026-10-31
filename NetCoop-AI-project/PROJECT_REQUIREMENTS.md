# NetCoop AI application requirements

This document records the requested product requirements, the hackathon requirements, and the implementation status in this project. “Implemented” means present in this build; it does not imply performance or diagnostic accuracy has been validated on a production network.

## Product purpose

NetCoop AI is an evidence-led network operations dashboard. It should help an operator review network measurements, correlate symptoms across supplied devices, understand likely causes and uncertainty, and receive safe next steps. It must distinguish actual measurements from synthetic demo fixtures and must not claim access to devices or services that have not supplied data.

## Functional requirements and status

| ID | Requirement | Status in this build |
|---|---|---|
| F-01 | Responsive, polished operations dashboard with overview, signal coverage, live stats, trends, devices, investigations, architecture, and six-step presentation guide. | Implemented. |
| F-02 | Read local Windows adapter, CPU/memory, byte-counter traffic, cached neighbors, and explicit Wi-Fi scan results. | Implemented for the computer running the local server. Cached neighbors are not active reachability checks. |
| F-03 | Automatically format traffic rates in appropriate bit-rate units and refresh local samples quickly. | Implemented; approximately two-second local sampling and automatic unit formatting. |
| F-04 | Import telemetry with timestamp, device, metric, value, unit, and source; reject missing or incompatible data. | Implemented with row-level errors. No implicit unit conversion. |
| F-05 | Show only supplied network topology relationships and device/service metrics. | Implemented for imported topology and metrics. No guessed router, modem, AP-client, DNS, DHCP, database, or service-pool status. |
| F-06 | Retain investigation history, task status, execution events, and report results. | Implemented in local SQLite. |
| F-07 | Use multiple cooperating diagnostic agents and structured messages. | Implemented as three in-process deterministic agents (performance, infrastructure health, connectivity) plus correlation/reporting. It is not a hosted LLM or a five-agent deployment. |
| F-08 | Validate and correlate agent evidence, retain alternatives/conflicts, and report insufficient evidence when appropriate. | Implemented with deterministic rules. Confidence is uncalibrated and diagnostic accuracy has not been evaluated on production data. |
| F-09 | Offer a downloadable structured JSON diagnosis report. | Implemented at `GET /api/tasks/{id}/report.json`; report schema is in `schemas/report.schema.json`. |
| F-10 | Present service health on a 0–100 scale. | Implemented as a coverage-adjusted heuristic. It is explicitly uncalibrated; missing telemetry is not treated as confirmed healthy. |
| F-11 | Diagnose supplied evidence for link congestion, weak Wi-Fi, interface faults, device/server status, DNS/DHCP/database status, and connection-pool use. | Rule patterns and opt-in fixtures exist. Real diagnosis requires those measurements/statuses from an authorized source. |
| F-12 | Provide explicit demonstration inputs and repeatable checks without contaminating live telemetry. | Implemented. Synthetic fixtures are opt-in, labeled, and stored as demo investigations rather than live telemetry. |
| F-13 | Support traffic shifting when abnormal load is observed. | Not enabled. No route/controller write operations are implemented. A 200 GB file size alone is not a congestion signal. |
| F-14 | Allow other users to access the dashboard with credentials. | Not implemented in this local build. It binds to loopback; shared use requires a separately secured HTTPS deployment and authentication. |
| F-15 | Connect a Cisco Catalyst SD-WAN Manager. | Optional read-only hardware-health connector, configured with server-side HTTPS environment variables. It is not configured by default and does not provide path steering. |

## Required six-part presentation flow

The presentation guide contains these six sections:

1. Problem and Introduction
2. Our Solution
3. System Architecture
4. Live Demonstration
5. Technical Decisions and Reliability
6. Results and Conclusion

The demo uses either actual imported/local evidence or an explicitly labeled synthetic scenario. It must not present synthetic readings as live network measurements.

## Hackathon report and interoperability requirements

The report must contain `incident_id`, `status`, `suspected_root_cause`, `confidence`, `affected_devices`, `supporting_evidence`, `alternative_causes`, `recommended_actions`, `evidence_sources`, and `limitations`. The schema may also carry cause code, confidence breakdown, conflict information, and other defined fields. See `schemas/report.schema.json`.

Agent messages use the documented `ncmp/1.0` JSON envelope, with meanings and units described in `docs/agent-protocol.md` and `schemas/message.schema.json`. Findings must be validated before correlation. The conflict round rechecks competing explanations against the captured evidence; it must not claim a new device poll when none occurred.

The automated checks cover agent messages, report fields/schema, confidence and missing-data behavior, service-health coverage, malformed CSV, and incompatible units. Synthetic cases cover normal readings, congestion, weak Wi-Fi, interface fault, DNS/DHCP, server downtime, database failure, pool exhaustion, agent disagreement, and missing data. These are reproducibility fixtures, not a production benchmark or calibrated evaluation.

## Safety, privacy, and evidence rules

- Do not fabricate device readings, topology edges, service status, successful tool results, or diagnostic certainty.
- Label generated sample scenarios as synthetic and keep them out of live telemetry.
- Keep controller credentials on the server and use a read-only account for the current Cisco connector.
- This build performs no route or hardware changes.
- Do not expose the local HTTP server to a LAN or the Internet. Use an authenticated HTTPS deployment for team access.
- Network-wide router/modem attribution requires an authorized telemetry source or controller that supplies device identity, topology, and measurements.

## Runtime requirements

- Python 3.9 or newer.
- Python standard library only; there are no third-party Python packages to install.
- Windows is required for the current OS-specific adapter, neighbor-cache, and WLAN survey features. CSV telemetry analysis and the local web dashboard use Python's standard library.
- Start from this project directory with `python server.py`, then open `http://localhost:8000`.
- Run the existing checks with `python -m unittest discover -s tests -v`.
- Run one offline fixture with `python demo.py link_congestion`.

See `README.md` for detailed setup, API, telemetry format, and Cisco configuration instructions.
