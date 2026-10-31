# Agent workflow and interoperability

## Current implementation

The local workflow is deterministic Python with SQLite and a plain JavaScript dashboard. The five roles are telemetry/performance, infrastructure health, connectivity scope, fault correlation, and report validation. They run in-process over one validated telemetry snapshot; no LLM makes a diagnostic decision. This is a modular workflow, not a distributed agent service.

The first three roles receive distinct metric/topology slices and emit `ncmp/1.0` JSON findings to correlation. Correlation ranks only the rule patterns documented below. The report validator checks the required report fields and confidence range before the task is marked complete. The dashboard shows findings and a message trace; each completed task has a downloadable JSON report.

## Message envelope

See `../schemas/message.schema.json`. Every message has a protocol version, UUID, incident/task identifiers, message type, sender, recipient, and object payload. Numeric telemetry must retain its declared unit and source. Timestamps are UTC ISO 8601. A finding uses an agent status (`ok`, `no_data`, or `degraded`) and the observation slice that agent was assigned.

Canonical metric names include `latency_ms`, `jitter_ms`, `packet_loss_pct`, `throughput_mbps`, `bandwidth_mbps`, `link_utilization_pct`, `rssi_dbm`, `snr_db`, `retransmission_pct`, `cpu_pct`, `mem_pct`, `queue_drops`, `interface_errors`, and categorical `device_status`.

Service checks may additionally report categorical `server_status`, `dns_status`, `dhcp_status`, `database_status`, or numeric `connection_pool_usage_pct`, `connection_pool_active`, `connection_pool_max`, and `database_query_latency_ms`. Status values accepted are `up`, `down`, `degraded`, `ok`, `failed`, `failure`, `error`, `critical`, `warning`, `healthy`, `success`, and `passed`. Percent metrics must be 0-100; counts cannot be negative. Every row still requires timestamp, device ID, value, unit, and source. No unit is guessed or silently converted.

## Root-cause rules and confidence

The correlation role currently recognizes combined baseline deviations for link congestion (utilization plus queue drops and/or latency/jitter), weak Wi-Fi (RSSI plus retransmissions), interface fault (errors plus packet loss), and device overload (CPU/memory plus latency/loss). Explicit failed server, DNS, DHCP, and database status readings produce their corresponding service finding. Connection pool usage at or above 95% is a documented initial rule; tune it to the actual service's pool configuration.

Confidence is a rule support score: supporting signature coverage multiplied by agreement among ranked candidates and capped at 0.90. It is not a probability and has not been calibrated on a labeled network benchmark. A lone unexplained anomaly produces `insufficient_evidence`; no anomaly with a sufficient historical baseline produces `no_fault_found`. A task with no measurements returns `insufficient_evidence`.

The service health score is an evidence-coverage-adjusted indicator from 0 to 100. It uses eight components when supplied: server, DNS, database, connection-pool usage, CPU, memory, latency, and packet loss. The mean component score is multiplied by the fraction of components actually observed. Missing components therefore lower the score and are shown as missing coverage. It is not an SLA or statistically calibrated probability. The pool and host resource bands are initial rules, not universal operating limits.

## Boundaries

The local Windows sampler measures the computer running this app. It cannot see another server's application pool, DNS checks, database, router interface counters, AP client list, or path health. Those require an authorized collector/controller that supplies those fields. The current Cisco SD-WAN reader is read-only hardware health only. The app does not make route or hardware changes.
