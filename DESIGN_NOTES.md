# Design and trade-offs

- **SQLite + CSV + stdlib:** fully local and easy to run from a clean machine; trades away concurrency and warehouse-scale execution.
- **Two source feeds:** customer master plus order lifecycle events exercise both reference loading and event facts without external credentials.
- **Event grain:** preserves history and handles late/out-of-order events naturally. A fact row means one lifecycle event, not one current order.
- **Integer cents:** deterministic sums; values with more than two decimal places are rounded half-up. This assumes two decimal currency precision and does not model currency codes or FX.
- **Strict header contract:** schema drift fails loudly rather than silently dropping/guessing fields. Row-level quality issues are quarantined with raw values.
- **Atomic batch:** data writes and success metrics share a transaction; failed attempts preserve run status separately. There is no mid-file checkpoint.
- **Idempotency:** stable event IDs are unique and upserted. Within-file duplicate IDs keep the first row and quarantine later occurrences. This assumes source IDs are globally stable and unique.
- **Customer history:** Type 1 latest-update-wins is sufficient for a current customer dimension but cannot reproduce historical attributes. Use a Type 2 dimension if historical attribution is required.
- **Scale path:** generator supports 100k+ events; for higher volumes, bulk staging and set-based validation are the first optimization before adopting orchestration or distributed processing.
