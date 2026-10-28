"""Small, restartable CSV-to-SQLite dimensional data pipeline."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

CUSTOMER_COLUMNS = {"customer_id", "customer_name", "email", "country", "updated_at"}
ORDER_COLUMNS = {"event_id", "order_id", "customer_id", "event_ts", "status", "quantity", "unit_price", "source_file"}
VALID_STATUS = {"placed", "shipped", "delivered", "cancelled", "returned"}
LOG = logging.getLogger("order_pipeline")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fingerprint(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path: Path, required: set[str]):
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"{path}: missing header")
        missing = required - set(reader.fieldnames)
        extra = set(reader.fieldnames) - required
        if missing or extra:
            raise ValueError(f"{path}: schema mismatch; missing={sorted(missing)}, unexpected={sorted(extra)}")
        yield from reader


def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
      CREATE TABLE IF NOT EXISTS dim_customer (
        customer_key INTEGER PRIMARY KEY, customer_id TEXT NOT NULL UNIQUE,
        customer_name TEXT NOT NULL, email TEXT NOT NULL, country TEXT NOT NULL,
        source_updated_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS fact_order_event (
        event_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, customer_key INTEGER NOT NULL,
        event_ts TEXT NOT NULL, event_date TEXT NOT NULL, status TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0),
        revenue_cents INTEGER NOT NULL, source_file TEXT NOT NULL, run_id TEXT NOT NULL,
        FOREIGN KEY(customer_key) REFERENCES dim_customer(customer_key)
      );
      CREATE INDEX IF NOT EXISTS ix_fact_event_date ON fact_order_event(event_date);
      CREATE TABLE IF NOT EXISTS pipeline_run (
        run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT,
        status TEXT NOT NULL, customers_read INTEGER DEFAULT 0, events_read INTEGER DEFAULT 0,
        events_loaded INTEGER DEFAULT 0, rejected INTEGER DEFAULT 0, duplicate_events INTEGER DEFAULT 0,
        customer_count INTEGER DEFAULT 0, source_fingerprint TEXT NOT NULL, failure_reason TEXT
      );
      CREATE TABLE IF NOT EXISTS rejected_record (
        reject_id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, source_file TEXT NOT NULL,
        source_row INTEGER NOT NULL, entity TEXT NOT NULL, reason TEXT NOT NULL,
        raw_record TEXT NOT NULL, rejected_at TEXT NOT NULL,
        FOREIGN KEY(run_id) REFERENCES pipeline_run(run_id)
      );
    """)
    return conn


def cents(value: str) -> int:
    amount = Decimal(value)
    if not amount.is_finite() or amount < 0:
        raise ValueError("unit_price must be a finite non-negative amount")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def valid_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("event_ts must include timezone")
    return dt.astimezone(timezone.utc)


def run_pipeline(customers_csv: Path, events_csv: Path, db_path: Path, reject_csv: Path | None = None) -> dict:
    run_id = str(uuid.uuid4())
    started = now_iso()
    source_hash = hashlib.sha256((fingerprint(customers_csv) + fingerprint(events_csv)).encode()).hexdigest()
    conn = connect(db_path)
    stats = {"run_id": run_id, "started_at": started, "customers_read": 0, "events_read": 0,
             "events_loaded": 0, "rejected": 0, "duplicate_events": 0, "customer_count": 0}
    rejects: list[dict] = []
    conn.execute("INSERT INTO pipeline_run(run_id,started_at,status,source_fingerprint) VALUES(?,?,?,?)",
                 (run_id, started, "running", source_hash))
    conn.commit()
    try:
        customer_rows = list(rows(customers_csv, CUSTOMER_COLUMNS))
        event_rows = list(rows(events_csv, ORDER_COLUMNS))
        stats["customers_read"], stats["events_read"] = len(customer_rows), len(event_rows)
        conn.execute("BEGIN")
        seen_customers = set()
        for i, row in enumerate(customer_rows, 2):
            stats["customer_count"] += 1
            cid = (row.get("customer_id") or "").strip()
            reason = None
            if not cid or not row.get("customer_name", "").strip() or not row.get("country", "").strip():
                reason = "missing_required_customer_field"
            elif cid in seen_customers:
                reason = "duplicate_customer_id_in_batch"
            elif not row.get("updated_at", "").strip():
                reason = "missing_updated_at"
            if reason:
                rejects.append(dict(source_file=str(customers_csv), source_row=i, entity="customer", reason=reason, raw_record=row))
                continue
            seen_customers.add(cid)
            conn.execute("""INSERT INTO dim_customer(customer_id,customer_name,email,country,source_updated_at)
              VALUES(?,?,?,?,?) ON CONFLICT(customer_id) DO UPDATE SET
              customer_name=excluded.customer_name,email=excluded.email,country=excluded.country,
              source_updated_at=excluded.source_updated_at
              WHERE excluded.source_updated_at >= dim_customer.source_updated_at""",
              (cid, row["customer_name"].strip(), row.get("email", "").strip(), row["country"].strip(), row["updated_at"].strip()))

        seen_events = set()
        for i, row in enumerate(event_rows, 2):
            raw_event_id = (row.get("event_id") or "").strip()
            stats["events_read"] += 0
            reason = None
            if not raw_event_id or not (row.get("order_id") or "").strip() or not (row.get("customer_id") or "").strip():
                reason = "missing_required_field"
            elif raw_event_id in seen_events:
                stats["duplicate_events"] += 1
                reason = "duplicate_event_id_in_batch"
            elif row.get("status", "").strip().lower() not in VALID_STATUS:
                reason = "invalid_status"
            elif not conn.execute("SELECT 1 FROM dim_customer WHERE customer_id=?", ((row.get("customer_id") or "").strip(),)).fetchone():
                reason = "unknown_customer_id"
            try:
                event_dt = valid_ts((row.get("event_ts") or "").strip())
                qty = int(row.get("quantity", ""))
                price = cents(row.get("unit_price", ""))
                if qty <= 0:
                    raise ValueError("quantity must be positive")
            except (ValueError, InvalidOperation, OverflowError):
                event_dt, qty, price = None, 0, 0
                reason = reason or "invalid_timestamp_quantity_or_price"
            if reason:
                rejects.append(dict(source_file=(row.get("source_file") or str(events_csv)), source_row=i,
                                    entity="order_event", reason=reason, raw_record=row))
                continue
            seen_events.add(raw_event_id)
            customer = conn.execute("SELECT customer_key FROM dim_customer WHERE customer_id=?", (row["customer_id"].strip(),)).fetchone()
            revenue = qty * price
            conn.execute("""INSERT INTO fact_order_event VALUES(?,?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(event_id) DO UPDATE SET order_id=excluded.order_id,customer_key=excluded.customer_key,
              event_ts=excluded.event_ts,event_date=excluded.event_date,status=excluded.status,quantity=excluded.quantity,
              unit_price_cents=excluded.unit_price_cents,revenue_cents=excluded.revenue_cents,
              source_file=excluded.source_file,run_id=excluded.run_id""",
              (raw_event_id, row["order_id"].strip(), customer[0], event_dt.isoformat().replace("+00:00", "Z"),
               event_dt.date().isoformat(), row["status"].strip().lower(), qty, price, revenue,
               (row.get("source_file") or events_csv.name).strip(), run_id))
            stats["events_loaded"] += 1

        for rejection in rejects:
            conn.execute("INSERT INTO rejected_record(run_id,source_file,source_row,entity,reason,raw_record,rejected_at) VALUES(?,?,?,?,?,?,?)",
                         (run_id, rejection["source_file"], rejection["source_row"], rejection["entity"], rejection["reason"],
                          json.dumps(rejection["raw_record"], sort_keys=True), now_iso()))
        stats["rejected"] = len(rejects)
        conn.execute("UPDATE pipeline_run SET ended_at=?,status='success',customers_read=?,events_read=?,events_loaded=?,rejected=?,duplicate_events=?,customer_count=? WHERE run_id=?",
                     (now_iso(), stats["customers_read"], stats["events_read"], stats["events_loaded"], stats["rejected"],
                      stats["duplicate_events"], stats["customer_count"], run_id))
        conn.commit()
    except Exception as exc:
        conn.rollback()
        conn.execute("UPDATE pipeline_run SET ended_at=?,status='failed',customers_read=?,events_read=?,rejected=?,failure_reason=? WHERE run_id=?",
                     (now_iso(), stats["customers_read"], stats["events_read"], len(rejects), str(exc), run_id))
        conn.commit()
        raise
    finally:
        conn.close()
    if reject_csv is not None:
        reject_csv.parent.mkdir(parents=True, exist_ok=True)
        with reject_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["run_id", "source_file", "source_row", "entity", "reason", "raw_record"])
            writer.writeheader()
            for rej in rejects:
                writer.writerow({"run_id": run_id, **rej, "raw_record": json.dumps(rej["raw_record"], sort_keys=True)})
    return stats


def main():
    parser = argparse.ArgumentParser(description="Load order event and customer CSVs into a SQLite star schema")
    parser.add_argument("--customers", type=Path, default=Path("data/sample/customers.csv"))
    parser.add_argument("--events", type=Path, default=Path("data/sample/order_events.csv"))
    parser.add_argument("--db", type=Path, default=Path("outputs/warehouse.sqlite"))
    parser.add_argument("--rejects", type=Path, default=Path("outputs/rejects.csv"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    started = time.perf_counter()
    result = run_pipeline(args.customers, args.events, args.db, args.rejects)
    result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
