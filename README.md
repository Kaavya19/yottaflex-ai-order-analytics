# YottaFlex AI — Order Analytics Mini Platform

A reproducible, local data engineering vertical slice. It ingests **customer master** and **order event** CSVs, validates them, quarantines bad rows, upserts a small dimensional model in SQLite, and records operational metrics. Python 3.10+; runtime uses only the standard library.

## Run it

From the repository root:

```powershell
python -m unittest discover -s tests -v
python -m src.pipeline
```

The default run reads `data/sample/customers.csv` and `data/sample/order_events.csv`; it creates `outputs/warehouse.sqlite` and `outputs/rejects.csv`. A successful run prints a JSON metrics summary. Run it again to verify that the four facts remain four. `--customers`, `--events`, `--db`, and `--rejects` override the paths. Run `python tools/reconcile.py` to write the SQL-based checks to `outputs/sample_reconciliation.json`.

Generate and load 100,000 events (seeded, with a larger customer dimension):

```powershell
python tools/generate_data.py --rows 100000 --seed 73 --out data/generated
python -m src.pipeline --customers data/generated/customers.csv --events data/generated/order_events.csv --db outputs/large.sqlite --rejects outputs/large_rejects.csv
```

To add one deliberately invalid record to a generated batch, add `--include-invalid`. The generator produces valid event IDs and customer references otherwise. Python's standard `unittest` is the only test dependency.

## Architecture

```text
customers.csv ─┐                 ┌─ rejected_record table + rejects.csv
               ├─ schema checks ─┤
order_events ──┘  row/business QA ├─ SQLite: dim_customer ─┐
                                 └─ run metrics          └─ fact_order_event
                                                            ↓
                                                     SQL/report queries
```

The customer master is applied before events so foreign keys can be checked. Both source files are read as a batch, then customer upserts, facts, rejects, and success metrics commit in one transaction. A schema-level failure rolls back that batch and writes a failed `pipeline_run` record separately. This is intentionally a local single-process example, not a distributed orchestrator.

## Grain, keys, and rules

| Model | Grain / key | Important fields and rules |
|---|---|---|
| `dim_customer` | One current row per `customer_id`; integer surrogate `customer_key` | Customer ID is unique; name/country required; latest `updated_at` wins. |
| `fact_order_event` | One order lifecycle event per `event_id` | Customer FK must resolve; status in placed/shipped/delivered/cancelled/returned; quantity > 0; unit price is non-negative and stored in integer cents; event timestamp must include a timezone and is normalized to UTC. |
| `pipeline_run` | One row per execution `run_id` | UTC start/end timestamps, source fingerprint, counts, status and failure reason. |
| `rejected_record` | One rejected source row per run | Source file, one-based CSV line number (header is line 1), entity, reason and JSON copy of raw fields. |

Order events are immutable business events: out-of-order timestamps are retained as supplied and `event_date` is derived in UTC. The fact table is not an order snapshot; sum revenue only for the desired event/status grain. Revenue is quantity × unit price for each event, so lifecycle events can repeat the order amount. Duplicate event IDs within the same batch are rejected after the first occurrence. Existing IDs are upserted on rerun, preventing extra fact rows. Exact source schemas are enforced; missing or unexpected columns fail the batch visibly. Missing field values and business-rule failures are quarantined row by row.

Customer dimension is Type 1 for this small slice: a newer master record overwrites the current attributes. Historical customer attributes would require a Type 2 dimension or a separate change-event source. Source-file lineage is retained on facts; input file hashes are combined into `source_fingerprint` on each run.

## Queries and evidence

Example query (using Python's `sqlite3` or a SQLite client):

```sql
SELECT event_date, status, COUNT(*) AS events,
       SUM(revenue_cents) AS revenue_cents
FROM fact_order_event
GROUP BY event_date, status
ORDER BY event_date, status;

SELECT status, customers_read, events_read, events_loaded, rejected,
       duplicate_events, failure_reason
FROM pipeline_run ORDER BY started_at;
```

The sample has 3 unique customers and 7 event rows. Four events load and three rows are quarantined (second `EV004`, unknown customer `C999`, and zero quantity); **loaded event cents sum to 24,946**. Accepted counts plus rejected counts reconcile to input event rows. See `outputs/sample_run.json` and `outputs/sample_reconciliation.json` for captured run metrics and SQL assertions. Rejection detail is in `outputs/rejects.csv` and the database.

## Recovery, limits, and performance

Reruns are safe for facts because `event_id` is the primary key and loads upsert. Each attempt gets a new run ID; prior run history remains. On a failed batch, warehouse writes roll back and the run is marked failed with its reason. Correct the input and rerun. Backfills use the same path with explicit source paths and a separate DB or output folder if isolation is needed. There is no checkpointing within a source file, remote object store, scheduler, alerting service, or multi-writer support. Rejected rows from a schema-wide failure are not individually quarantined because the columns cannot be interpreted.

The fixed-seed 100,000-row run on the development environment completed in 2.875 seconds for 100,000 events and 10,000 customers (pipeline wall time, excluding data generation). For larger workloads the dominant current cost is per-row SQL execution and reference lookup. A reasonable next optimization is staging validated rows in bulk and joining customers in SQL, while preserving the same transactional and reject semantics. Avoid comparing run times across machines as a benchmark.

## AI use and review

AI assistance was used to scaffold this solution, suggest edge cases, and draft documentation. The complete user-provided prompts and an honest summary of review/validation are in [`PROMPT_HISTORY.md`](PROMPT_HISTORY.md). The candidate should personally review the code and be able to explain transaction boundaries, integer-cents arithmetic, duplicate policy, and limitations before submission.

