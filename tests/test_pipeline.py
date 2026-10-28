import csv
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from src.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "work")
        self.root = Path(self.temp.name)
        self.db = self.root / "warehouse.sqlite"
        self.customers = self.root / "customers.csv"
        self.events = self.root / "events.csv"
        self.write_customers([["C1", "Ada", "", "IN", "2026-10-20T00:00:00Z"]])

    def tearDown(self): self.temp.cleanup()

    def write_customers(self, records):
        with self.customers.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["customer_id", "customer_name", "email", "country", "updated_at"]); w.writerows(records)

    def write_events(self, records):
        with self.events.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["event_id", "order_id", "customer_id", "event_ts", "status", "quantity", "unit_price", "source_file"]); w.writerows(records)

    def test_sample_and_reconciliation(self):
        result = run_pipeline(ROOT / "data/sample/customers.csv", ROOT / "data/sample/order_events.csv", self.db)
        self.assertEqual(result["events_read"], 7)
        self.assertEqual(result["events_loaded"], 4)
        self.assertEqual(result["rejected"], 3)
        with closing(sqlite3.connect(self.db)) as c:
            self.assertEqual(c.execute("select count(*) from fact_order_event").fetchone()[0], 4)
            self.assertEqual(c.execute("select sum(revenue_cents) from fact_order_event").fetchone()[0], 24946)

    def test_empty_input_succeeds(self):
        self.write_events([])
        result = run_pipeline(self.customers, self.events, self.db)
        self.assertEqual((result["events_read"], result["events_loaded"], result["rejected"]), (0, 0, 0))

    def test_bad_timestamp_and_timezone_are_quarantined(self):
        self.write_events([["E1", "O1", "C1", "not-a-time", "placed", 1, "1.00", "x"],
                           ["E2", "O2", "C1", "2026-10-01T00:00:00", "placed", 1, "1.00", "x"]])
        result = run_pipeline(self.customers, self.events, self.db)
        self.assertEqual(result["rejected"], 2)

    def test_duplicate_id_and_boundary_values(self):
        self.write_events([["E1", "O1", "C1", "2026-10-01T00:00:00Z", "placed", 1, "0.00", "x"],
                           ["E1", "O1", "C1", "2026-10-01T00:01:00Z", "shipped", 1, "1.00", "x"]])
        result = run_pipeline(self.customers, self.events, self.db)
        self.assertEqual((result["events_loaded"], result["duplicate_events"], result["rejected"]), (1, 1, 1))
        with closing(sqlite3.connect(self.db)) as c: self.assertEqual(c.execute("select revenue_cents from fact_order_event").fetchone()[0], 0)

    def test_missing_null_and_bad_reference_quarantined(self):
        self.write_events([["E1", "", "C1", "2026-10-01T00:00:00Z", "placed", 1, "1.00", "x"],
                           ["E2", "O2", "C404", "2026-10-01T00:00:00Z", "placed", 1, "1.00", "x"]])
        self.assertEqual(run_pipeline(self.customers, self.events, self.db)["rejected"], 2)

    def test_rerun_is_idempotent(self):
        self.write_events([["E1", "O1", "C1", "2026-10-01T00:00:00Z", "placed", 2, "3.25", "x"]])
        run_pipeline(self.customers, self.events, self.db)
        run_pipeline(self.customers, self.events, self.db)
        with closing(sqlite3.connect(self.db)) as c:
            self.assertEqual(c.execute("select count(*) from fact_order_event").fetchone()[0], 1)
            self.assertEqual(c.execute("select count(*) from pipeline_run where status='success'").fetchone()[0], 2)

    def test_schema_drift_is_failed_and_logged(self):
        self.events.write_text("unexpected,columns\na,b\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            run_pipeline(self.customers, self.events, self.db)
        with closing(sqlite3.connect(self.db)) as c: self.assertEqual(c.execute("select status from pipeline_run").fetchone()[0], "failed")

    def test_failed_batch_can_be_repaired_and_retried(self):
        self.events.write_text("event_id,unexpected\nE1,x\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            run_pipeline(self.customers, self.events, self.db)
        self.write_events([["E1", "O1", "C1", "2026-10-01T00:00:00Z", "placed", 1, "1.00", "x"]])
        result = run_pipeline(self.customers, self.events, self.db)
        self.assertEqual(result["events_loaded"], 1)
        with closing(sqlite3.connect(self.db)) as c:
            self.assertEqual(c.execute("select status from pipeline_run order by started_at").fetchall(), [("failed",), ("success",)])


if __name__ == "__main__": unittest.main()
