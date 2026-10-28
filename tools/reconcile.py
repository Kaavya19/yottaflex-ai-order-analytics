"""Produce a compact SQL-based reconciliation report for a loaded warehouse."""
import argparse
import json
import sqlite3
from pathlib import Path


def build_report(db: Path) -> dict:
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        latest = conn.execute("SELECT * FROM pipeline_run ORDER BY started_at DESC LIMIT 1").fetchone()
        facts = conn.execute("SELECT COUNT(*) AS fact_rows, COALESCE(SUM(revenue_cents),0) AS revenue_cents, COUNT(DISTINCT event_id) AS distinct_event_ids FROM fact_order_event").fetchone()
        rejects = conn.execute("SELECT COUNT(*) FROM rejected_record WHERE run_id=?", (latest["run_id"],)).fetchone()[0]
        event_rejects = conn.execute("SELECT COUNT(*) FROM rejected_record WHERE run_id=? AND entity='order_event'", (latest["run_id"],)).fetchone()[0]
        by_date_status = [dict(r) for r in conn.execute("SELECT event_date,status,COUNT(*) AS events,SUM(revenue_cents) AS revenue_cents FROM fact_order_event GROUP BY event_date,status ORDER BY event_date,status")]
        report = {"latest_run": dict(latest), "warehouse": dict(facts), "latest_run_reject_rows": rejects,
                  "event_reconciliation": {"input_rows": latest["events_read"], "loaded_rows": latest["events_loaded"],
                                           "rejected_rows": event_rejects,
                                           "balances": latest["events_read"] == latest["events_loaded"] + event_rejects},
                  "by_date_status": by_date_status}
        report["assertions"] = {"fact_keys_unique": facts["fact_rows"] == facts["distinct_event_ids"],
                                "all_fact_customer_keys_resolve": conn.execute("SELECT COUNT(*) FROM fact_order_event f LEFT JOIN dim_customer d USING(customer_key) WHERE d.customer_key IS NULL").fetchone()[0] == 0,
                                "reject_count_matches_run_metric": rejects == latest["rejected"]}
        report["assertions"]["all_pass"] = all(report["assertions"].values()) and report["event_reconciliation"]["balances"]
        return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--db", type=Path, default=Path("outputs/warehouse.sqlite")); p.add_argument("--out", type=Path, default=Path("outputs/sample_reconciliation.json"))
    args = p.parse_args(); report = build_report(args.db)
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["assertions"], indent=2))
