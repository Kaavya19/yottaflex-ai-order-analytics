"""Generate deterministic scale data. Invalid cases can be enabled explicitly."""
import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate(out: Path, n: int, seed: int = 73, include_invalid: bool = False):
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    customers = out / "customers.csv"
    events = out / "order_events.csv"
    with customers.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["customer_id", "customer_name", "email", "country", "updated_at"])
        for i in range(1, max(100, n // 10) + 1):
            w.writerow([f"C{i:06d}", f"Customer {i}", f"c{i}@example.test", rng.choice(["IN", "US", "GB", "DE"]), "2026-10-20T00:00:00Z"])
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with events.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["event_id", "order_id", "customer_id", "event_ts", "status", "quantity", "unit_price", "source_file"])
        for i in range(1, n + 1):
            dt = base + timedelta(minutes=rng.randrange(0, 400_000))
            w.writerow([f"EV{i:09d}", f"O{i:09d}", f"C{rng.randrange(1, max(100, n // 10) + 1):06d}",
                        dt.isoformat().replace("+00:00", "Z"), rng.choice(["placed", "shipped", "delivered", "cancelled"]),
                        rng.randint(1, 5), f"{rng.randint(100, 50000) / 100:.2f}", "generated_orders.csv"])
        if include_invalid:
            w.writerow(["EVBAD", "OBAD", "C999999", "not-a-date", "mystery", 0, "-1", "generated_orders.csv"])
    return customers, events


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--rows", type=int, default=100_000); p.add_argument("--seed", type=int, default=73)
    p.add_argument("--out", type=Path, default=Path("data/generated")); p.add_argument("--include-invalid", action="store_true")
    a = p.parse_args()
    if a.rows < 0: p.error("--rows must be non-negative")
    print(generate(a.out, a.rows, a.seed, a.include_invalid))
