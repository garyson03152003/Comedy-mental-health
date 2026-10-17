"""Age profile of each show's audience, calibrated to its reported Nielsen median viewer age.

Viewers at single-year age a  ~  ATUS TV minutes at age a (population-weighted) x exp(theta * a),
with theta solved so the audience's median age equals the show's reported median.
Intensity for an age group = the show's viewers in the group / the group's population share,
scaled so the population average is 1 ("relative viewing rate"). Multi-show events average their shows.
"""
import numpy as np, pandas as pd, pyreadr
from scipy.optimize import brentq

R = "data/raw/atus_pkg/atus/data/{}.rda"
act, resp, cps = (list(pyreadr.read_r(R.format(f)).values())[0] for f in ("atusact", "atusresp", "atuscps"))
tv = act[act.tiercode.isin([120303, 120304])].groupby("tucaseid").dur.sum()
d = resp[["tucaseid", "tuyear", "wt"]].merge(cps[["tucaseid", "age"]], on="tucaseid")
d["tv"] = d.tucaseid.map(tv).fillna(0)
d["age"] = d.age.clip(upper=85)

GROUPS = {
    "wonder": ([14, 24, 34, 44, 54, 64, 74, 84, 200],
               ["15-24 years", "25-34 years", "35-44 years", "45-54 years", "55-64 years", "65-74 years",
                "75-84 years", "85+ years"]),
    "brfss": ([17, 24, 29, 34, 39, 44, 49, 54, 59, 64, 69, 74, 79, 200], list(range(1, 14))),
}

def profile(year, median):
    x = d[d.tuyear.between(min(year, 2016) - 3, min(year, 2016))]
    pop = x.groupby("age").wt.sum()
    base = (x.wt * x.tv).groupby(x.age).sum()
    ages = base.index.values.astype(float)
    def med(theta):
        f = base.values * np.exp(theta * (ages - 50))
        c = np.cumsum(f) / f.sum()
        return ages[np.searchsorted(c, 0.5)] - median
    theta = brentq(med, -0.5, 0.5) if med(-0.5) * med(0.5) < 0 else 0.0
    viewers = pd.Series(base.values * np.exp(theta * (ages - 50)), index=base.index)
    return viewers / viewers.sum(), pop / pop.sum()

ev = pd.read_csv("data/show_events.csv", parse_dates=["start", "end"])
rows = []
for r in ev.itertuples():
    v, p = profile(r.start.year, r.median_age)
    for scheme, (bins, labels) in GROUPS.items():
        g = pd.cut(v.index, bins, labels=labels)
        rate = v.groupby(g, observed=True).sum() / p.groupby(g, observed=True).sum()
        for k, val in rate.items():
            rows.append(dict(event=r.event, show=r.show, scheme=scheme, group=str(k), rate=val))
prof = pd.DataFrame(rows).groupby(["event", "scheme", "group"], as_index=False).rate.mean()
prof.to_csv("results/show_age_profiles.csv", index=False)
if __name__ == "__main__":
    print(prof[prof.scheme == "wonder"].pivot(index="group", columns="event", values="rate").round(2).to_string())
