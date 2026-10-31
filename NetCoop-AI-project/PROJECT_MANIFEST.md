# NetCoop AI project file manifest

This manifest lists the files required to run, inspect, and verify the packaged application.

## Application source

- `server.py` — local HTTP server, telemetry APIs, orchestration, storage, and report generation.
- `demo.py` — command-line synthetic demonstration.
- `demo_scenarios.py` — opt-in synthetic scenario fixtures used by demos and checks.
- `web/index.html` — dashboard entry point.
- `web/app_live.js` — frontend application and interactions.
- `web/app_live.css`, `web/style.css`, `web/network.css` — dashboard styles.

## Protocol and validation

- `docs/agent-protocol.md` — agent message and field documentation.
- `schemas/message.schema.json` — structured agent message schema.
- `schemas/report.schema.json` — diagnostic JSON report schema.

## Setup and requirements

- `README.md` — installation/run steps, telemetry format, APIs, security notes, and optional Cisco setup.
- `PROJECT_REQUIREMENTS.md` — application and hackathon requirements with implementation status.
- `requirements.txt` — confirms Python standard library only; no pip packages are required.

## Verification

- `tests/test_agent_workflow.py` — automated workflow and API checks.
- `tests/README.md` — how to run tests and offline scenarios.
- `tests/__init__.py` — test package marker.

## Generated at runtime (not shipped)

- `netcoop.db` — created automatically by `server.py` in its working directory. It stores local telemetry and task history, so the package does not include any machine-specific database.
- `__pycache__` and other temporary files are not required.

## Start

Extract the ZIP, open PowerShell in the extracted project folder, and run:

```powershell
python server.py
```

Then open `http://localhost:8000`. Run checks with:

```powershell
python -m unittest discover -s tests -v
```
