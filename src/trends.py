"""Google Trends pre-strike popularity of late-night shows, by state and nationally.

For each strike, over the 12 months before it:
  * national: all hosts in one query, so their mean interest is comparable across shows;
  * by state: each host alone, giving a 0-100 index of how much that state searches for them
    relative to its total search volume (100 = the most interested state).
Results are cached in data/trends/ so reruns don't hit Google.
"""
import os, time, pandas as pd
from pytrends.request import TrendReq

SHOWS = {
    "wga2007": {"pre": "2006-11-01 2007-10-31",
                "terms": ["Jay Leno", "David Letterman", "Conan", "Jimmy Kimmel", "Daily Show"]},
    "wga2023": {"pre": "2022-05-01 2023-04-30",
                "terms": ["Jimmy Fallon", "Stephen Colbert", "Jimmy Kimmel", "Seth Meyers", "Daily Show"]},
}
OUT = "data/trends"
t = TrendReq(hl="en-US", tz=300, timeout=(10, 60))

def call(fn, *a, **k):
    for i in range(6):
        try:
            return fn(*a, **k)
        except Exception as e:  # 429s from Google: back off
            print("retry", i, e.__class__.__name__); time.sleep(30 * (i + 1))
    raise RuntimeError("Google Trends kept failing")

for strike, cfg in SHOWS.items():
    nat_path, reg_path = f"{OUT}/{strike}_national.csv", f"{OUT}/{strike}_states.csv"
    if not os.path.exists(nat_path):
        call(t.build_payload, cfg["terms"], timeframe=cfg["pre"], geo="US")
        call(t.interest_over_time).drop(columns="isPartial").mean().rename("interest").to_csv(nat_path)
        time.sleep(5)
    if not os.path.exists(reg_path):
        frames = []
        for term in cfg["terms"]:
            call(t.build_payload, [term], timeframe=cfg["pre"], geo="US")
            frames.append(call(t.interest_by_region, resolution="REGION", inc_low_vol=True)[term])
            time.sleep(5)
        pd.concat(frames, axis=1).to_csv(reg_path)
    print(strike, pd.read_csv(nat_path, index_col=0).T.round(1).to_string(), sep="\n")

# Long-run national monthly interest, 2004-2025, comparable across eras: two queries
# sharing "Jimmy Kimmel" as an anchor, the second rescaled onto the first.
lr_path = f"{OUT}/national_monthly_2004_2025.csv"
if not os.path.exists(lr_path):
    tf = "2004-01-01 2025-12-31"
    call(t.build_payload, ["Jay Leno", "David Letterman", "Jimmy Fallon", "Stephen Colbert", "Jimmy Kimmel"], timeframe=tf, geo="US")
    a = call(t.interest_over_time).drop(columns="isPartial"); time.sleep(5)
    call(t.build_payload, ["Jimmy Kimmel", "Conan", "Seth Meyers", "Daily Show"], timeframe=tf, geo="US")
    b = call(t.interest_over_time).drop(columns="isPartial")
    k = a["Jimmy Kimmel"].sum() / b["Jimmy Kimmel"].sum()
    pd.concat([a, (b * k).drop(columns="Jimmy Kimmel")], axis=1).to_csv(lr_path)
print(pd.read_csv(lr_path, index_col=0, parse_dates=True).resample("YE").mean().round(1).iloc[[3, 4, 18, 19]])
