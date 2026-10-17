"""South Park original air dates (regular episodes + specials) from the TVmaze API."""
import requests, pandas as pd

eps = requests.get("https://api.tvmaze.com/shows/112/episodes", params={"specials": 1}, timeout=60).json()
ep = pd.DataFrame([{"season": e["season"], "number": e["number"], "type": e["type"], "date": e["airdate"],
                    "name": e["name"]} for e in eps if e.get("airdate")])
# Paramount+ specials (2021-24) are filed under a separate "South Park Movies" entry
mv = requests.get("https://api.tvmaze.com/shows/59210/episodes", params={"specials": 1}, timeout=60).json()
ep = pd.concat([ep, pd.DataFrame([{"season": None, "number": None, "type": "streaming_special",
                                   "date": e["airdate"], "name": e["name"]} for e in mv if e.get("airdate")])], ignore_index=True)
ep["date"] = pd.to_datetime(ep.date)
ep = ep[ep.date <= pd.Timestamp.today()].sort_values("date")
ep.to_csv("data/southpark_episodes.csv", index=False)
if __name__ == "__main__":
    print(len(ep), "episodes;", ep.date.min().date(), "to", ep.date.max().date())
    print(ep[ep.date >= "2022-01-01"].groupby([ep.date.dt.to_period("M"), "type"]).size().unstack(fill_value=0).to_string())
