"""Wikipedia daily pageviews for late-night comedy shows (attention proxy), 2022-2025."""
import time, requests, pandas as pd

SHOWS = ["The_Tonight_Show_Starring_Jimmy_Fallon", "The_Late_Show_with_Stephen_Colbert",
         "Jimmy_Kimmel_Live!", "Late_Night_with_Seth_Meyers", "The_Daily_Show",
         "Saturday_Night_Live", "Last_Week_Tonight_with_John_Oliver"]
API = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
       "all-access/user/{}/daily/20220101/20251231")
HEADERS = {"User-Agent": "comedy-mental-health/0.1 (https://github.com/garyson03152003/comedy-mental-health) python-requests"}

rows = []
for s in SHOWS:
    for attempt in range(6):
        r = requests.get(API.format(requests.utils.quote(s, safe="")), headers=HEADERS, timeout=60)
        if r.status_code != 429:
            break
        time.sleep(5 * 2 ** attempt)
    if not r.ok:
        print('skipped', s, r.status_code)
        continue
    for it in r.json()["items"]:
        rows.append({"show": s, "date": pd.to_datetime(it["timestamp"][:8]), "views": it["views"]})
    time.sleep(2)
pd.DataFrame(rows).to_csv("results/pageviews_daily.csv", index=False)
print(pd.DataFrame(rows).groupby("show").views.sum())
