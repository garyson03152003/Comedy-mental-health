"""Google Trends weekly US interest in substitutes for late-night TV and South Park (2022-2025)."""
import os, time, pandas as pd
from pytrends.request import TrendReq

QUERIES = {
    "latenight_subs": ["Gutfeld", "The Office", "stand up comedy", "comedy podcast", "Jimmy Fallon"],  # "comedy podcast" too rare: all zeros
    "southpark_subs": ["South Park", "Family Guy", "Rick and Morty", "The Simpsons", "Bob's Burgers"],
}
t = TrendReq(hl="en-US", tz=300, timeout=(10, 60))
for k, kw in QUERIES.items():
    path = f"data/trends/{k}_weekly.csv"
    if os.path.exists(path): continue
    for i in range(6):
        try:
            t.build_payload(kw, timeframe="2022-01-01 2025-12-31", geo="US")
            t.interest_over_time().drop(columns="isPartial").to_csv(path); break
        except Exception as e:
            print("retry", e.__class__.__name__); time.sleep(30 * (i + 1))
    time.sleep(5)
    print(k, "ok")
