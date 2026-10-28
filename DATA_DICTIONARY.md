# Data dictionary

All table and column names use `snake_case`. CSV timestamps are ISO-8601; timestamps written to SQLite are UTC ISO-8601 strings ending in `Z`. Currency is represented as integer cents to avoid floating-point aggregation errors.

## Customer input — `customers.csv`

| Column | Type | Required | Meaning |
|---|---|---:|---|
| customer_id | string | yes | Stable natural key. |
| customer_name | string | yes | Display name. |
| email | string | no | Contact field; empty allowed. |
| country | string | yes | Country code/name from producer. |
| updated_at | ISO-8601 string | yes | Source update timestamp used for Type 1 freshness. |

## Event input — `order_events.csv`

| Column | Type | Required | Meaning |
|---|---|---:|---|
| event_id | string | yes | Stable unique event key and idempotency key. |
| order_id | string | yes | Business order identifier; multiple lifecycle events may share it. |
| customer_id | string | yes | Natural key reference to customer input. |
| event_ts | ISO-8601 with timezone | yes | Business event time; stored in UTC. |
| status | enum string | yes | placed, shipped, delivered, cancelled, returned. |
| quantity | positive integer | yes | Units on this event. |
| unit_price | decimal string | yes | Non-negative amount; converted to cents using decimal half-up rounding. |
| source_file | string | yes | Producer-provided lineage label. |

## Target tables

`dim_customer(customer_key INTEGER PK, customer_id TEXT UNIQUE, customer_name TEXT, email TEXT, country TEXT, source_updated_at TEXT)` is the current Type 1 customer dimension. `fact_order_event(event_id TEXT PK, order_id TEXT, customer_key INTEGER FK, event_ts TEXT, event_date TEXT, status TEXT, quantity INTEGER, unit_price_cents INTEGER, revenue_cents INTEGER, source_file TEXT, run_id TEXT)` is an event-grain fact. `pipeline_run` records lifecycle and aggregate metrics. `rejected_record` retains raw row JSON plus source location and reason.
