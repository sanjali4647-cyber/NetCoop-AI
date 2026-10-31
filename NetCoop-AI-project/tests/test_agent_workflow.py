import json
import http.client
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

import server as app
from demo_scenarios import make_rows


def diagnose(name):
    result, events = app.task_result(name, samples=make_rows(name))
    report = app.diagnostic_report("TEST-" + name.upper(), result)
    app.validate_report(report)
    return result, events, report


class AgentWorkflowTests(unittest.TestCase):
    def test_link_congestion_report_contains_required_fields(self):
        result, events, report = diagnose("link_congestion")
        self.assertEqual(report["root_cause_code"], "link_congestion")
        self.assertEqual(len(report["supporting_evidence"]), 3)
        self.assertIn("affected_devices", report)
        self.assertTrue(any(e["name"] == "Evidence correlation" for e in events))

    def test_distinct_agents_emit_versioned_messages(self):
        result, _, _ = diagnose("link_congestion")
        senders = {message["sender"] for message in result["message_log"]}
        self.assertTrue({"performance_agent", "infrastructure_health_agent", "connectivity_agent", "correlation_agent"}.issubset(senders))
        self.assertTrue(all(message["protocol"] == "ncmp/1.0" for message in result["message_log"]))

    def test_fault_scenarios(self):
        expected = {"weak_wifi": "weak_wifi_signal", "interface_fault": "interface_fault", "dns_failure": "dns_failure", "dhcp_failure": "dhcp_failure", "server_downtime": "server_downtime", "database_failure": "database_failure", "connection_pool_exhaustion": "connection_pool_exhaustion"}
        for scenario, cause in expected.items():
            with self.subTest(scenario=scenario):
                _, _, report = diagnose(scenario)
                self.assertEqual(report["root_cause_code"], cause)

    def test_normal_and_missing_data_are_honest(self):
        _, _, normal = diagnose("normal")
        self.assertEqual(normal["status"], "no_fault_found")
        _, _, missing = diagnose("missing")
        self.assertEqual(missing["status"], "insufficient_evidence")
        self.assertIsNone(missing["confidence"])

    def test_service_score_exposes_partial_coverage(self):
        rows = make_rows("connection_pool_exhaustion")
        summary = app.service_health_summary(rows)
        self.assertEqual(summary["devices"][0]["score"], 0)
        self.assertEqual(summary["devices"][0]["coverage"], 0.12)
        self.assertEqual(summary["devices"][0]["expected_components"], 8)

    def test_conflict_round_uses_structured_probe_messages(self):
        old_db = app.DB
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "work") as folder:
            app.DB = Path(folder) / "workflow.db"
            app.init_db()
            task_id = "12345678-conflict-test"
            conn = app.connect()
            conn.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?)", (task_id, "compare competing causes", "conflict test", "Running", 0, None, "[]"))
            conn.executemany("INSERT INTO telemetry(timestamp,device_id,metric,value,unit,source,parent_device_id,path_id) VALUES(?,?,?,?,?,?,?,?)", [(r['timestamp'],r['device_id'],r['metric'],r['value'],r['unit'],r['source'],r['parent_device_id'],r['path_id']) for r in make_rows('agents_disagree')])
            conn.commit()
            conn.close()
            try:
                app.run_task(task_id, "compare competing causes")
                conn = app.connect()
                row = conn.execute("SELECT result,events FROM tasks WHERE id=?", (task_id,)).fetchone()
                conn.close()
                result = json.loads(row["result"])
                events = json.loads(row["events"])
                types = [x["type"] for x in result["message_log"]]
                self.assertIn("conflict_notice", types)
                self.assertIn("probe_request", types)
                self.assertIn("probe_response", types)
                self.assertTrue(any(x["name"] == "Conflict round completed" for x in events))
            finally:
                app.DB = old_db

    def test_report_validator_rejects_missing_required_data(self):
        with self.assertRaises(ValueError):
            app.validate_report({"incident_id": "x"})

    def test_report_matches_published_json_schema(self):
        _, _, report = diagnose("link_congestion")
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "report.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertTrue(set(schema["required"]).issubset(report))
        self.assertTrue(set(report).issubset(set(schema["properties"])))


class TelemetryImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_db = app.DB
        cls.temp_dir = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "work")
        app.DB = Path(cls.temp_dir.name) / "test.db"
        app.init_db()
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.http.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(timeout=2)
        app.DB = cls.old_db
        cls.temp_dir.cleanup()

    def post_csv(self, body):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request("POST", "/api/telemetry/import", body=body, headers={"Content-Type": "text/csv"})
        response = conn.getresponse()
        result = json.loads(response.read())
        conn.close()
        return response.status, result

    def test_missing_fields_are_rejected_with_explanation(self):
        status, result = self.post_csv("timestamp,device_id\n2026-01-01T00:00:00Z,sw1\n")
        self.assertEqual(status, 400)
        self.assertIn("Missing required columns", result["error"])

    def test_incompatible_units_are_rejected_not_silently_converted(self):
        header = "timestamp,device_id,metric,value,unit,source\n"
        status, _ = self.post_csv(header + "2026-01-01T00:00:00Z,app1,cpu_pct,50,percent,fixture\n")
        self.assertEqual(status, 201)
        status, result = self.post_csv(header + "2026-01-01T00:01:00Z,app1,cpu_pct,0.5,fraction,fixture\n")
        self.assertEqual(status, 400)
        self.assertIn("unit mismatch", " ".join(result.get("row_errors", [])))

    def test_task_report_endpoint_downloads_structured_json(self):
        task_id = "report-download-test"
        result = {"json_report": app.diagnostic_report("INC-TEST", {"status": "insufficient_evidence", "anomalies": [], "agent_findings": []})}
        conn = app.connect()
        conn.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?)", (task_id, "test", "report test", "Completed", 0, json.dumps(result), "[]"))
        conn.commit()
        conn.close()
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request("GET", f"/api/tasks/{task_id}/report.json")
        response = conn.getresponse()
        report = json.loads(response.read())
        self.assertEqual(response.status, 200)
        self.assertIn("attachment; filename=", response.getheader("Content-Disposition"))
        self.assertEqual(report["incident_id"], "INC-TEST")
        conn.close()


if __name__ == "__main__":
    unittest.main()
