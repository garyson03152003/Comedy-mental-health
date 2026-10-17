"""Monthly US suicide deaths around comedy/late-night TV hiatuses (CDC WONDER, national).

Model: log(suicides per day) in month t = beta * hiatus share of month + year FE + calendar-month FE.
Inference by randomization: the same-length hiatus is placed at every possible start month in
non-event years and the real estimate is ranked against that placebo distribution.
"""
import re
import numpy as np, pandas as pd, pyfixest as pf
from events import EVENTS

def load(path):
    raw = pd.read_csv(path, header=0, dtype=str)
    rows, month = [], None
    for r in raw.itertuples(index=False):
        cells = [c for c in r if isinstance(c, str)]
        if re.match(r"^[A-Z][a-z]{2}\.?,? \d{4}", cells[0]):
            month, cells = cells[0], cells[1:]
        rows.append((month, cells[0], cells[1]))
    d = pd.DataFrame(rows, columns=["label", "age", "deaths"])
    d["month"] = pd.to_datetime(d.label.str.extract(r"^(\w+)\.?,? (\d{4})").agg(" ".join, axis=1), format="%b %Y")
    d["partial"] = d.label.str.contains("partial")
    d["deaths"] = pd.to_numeric(d.deaths.str.replace(",", ""), errors="coerce")  # 'Suppressed' -> NaN
    return d


a = load("data/wonder/d76_month_age.csv"); a = a[a.month < "2018-01-01"]
b = load("data/wonder/d176_month_age.csv"); b = b[~b.partial]
d = pd.concat([a, b])
d = d[(d.month < "2026-01-01") & (d.age != "Not Stated")]
d["older"] = d.age.isin(["55-64 years", "65-74 years", "75-84 years", "85+ years"])

def share(months, start, end):
    """Share of each calendar month's days inside [start, end)."""
    m0 = months.values.astype("datetime64[D]")
    m1 = (months + pd.offsets.MonthBegin(1)).values.astype("datetime64[D]")
    lo, hi = np.maximum(m0, np.datetime64(start, "D")), np.minimum(m1, np.datetime64(end, "D"))
    return np.clip((hi - lo).astype(int), 0, None) / (m1 - m0).astype(int)

def panel(group=None):
    x = d if group is None else d[d.older == group]
    p = x.groupby("month", as_index=False).deaths.sum()
    p["ndays"] = p.month.dt.days_in_month
    p["y"] = np.log(p.deaths / p.ndays)
    p["year"], p["moy"] = p.month.dt.year, p.month.dt.month
    return p

def est(p, start, end, fe="year + moy"):
    q = p.assign(exp=share(p.month, start, end))
    return pf.feols(f"y ~ exp | {fe}", data=q, vcov="hetero").coef()["exp"]

EVENT_YEARS = {2007, 2008, 2023, 2025}
def placebo(p, length_days, fe="year + moy"):
    out = []
    for start in pd.date_range("1999-01-01", "2025-06-01", freq="MS"):
        end = start + pd.Timedelta(days=length_days)
        if {start.year, end.year} & EVENT_YEARS or start.year == 2020 or end > pd.Timestamp("2025-12-31"):
            continue  # keep fake windows away from the real events and COVID onset
        out.append(est(p, start, end, fe))
    return np.array(out)

if __name__ == "__main__":
    rows = []
    for label, ev in [("2023 strike (late night)", "wga2023_latenight"),
                      ("2007-08 strike (late night)", "wga2007_latenight"),
                      ("2007-08 strike (scripted + late night)", "wga2007_scripted"),
                      ("Kimmel suspension 2025", "kimmel2025")]:
        s, e = (pd.Timestamp(t) for t in EVENTS[ev])
        for grp_name, grp in [("all ages", None), ("55+", True), ("under 55", False)]:
            p = panel(grp)
            b = est(p, s, e)
            pl = placebo(p, (e - s).days)
            rows.append(dict(event=label, group=grp_name, pct_change=100 * (np.exp(b) - 1),
                             placebo_sd_pct=100 * pl.std(), placebo_p=(np.abs(pl) >= abs(b)).mean(),
                             n_placebos=len(pl)))
            print(f"{label:40s} {grp_name:9s} {100*(np.exp(b)-1):+6.2f}%  placebo SD {100*pl.std():.2f}%  "
                  f"p={(np.abs(pl) >= abs(b)).mean():.2f}")

    # older-vs-younger gap (triple-difference analogue): log(older) - log(younger)
    po, py = panel(True), panel(False)
    gap = po[["month", "year", "moy"]].assign(y=po.y.values - py.set_index("month").loc[po.month, "y"].values)
    for label, ev in [("2023 strike", "wga2023_latenight"), ("2007-08 strike", "wga2007_scripted")]:
        s, e = (pd.Timestamp(t) for t in EVENTS[ev])
        b, pl = est(gap, s, e), placebo(gap, (e - s).days)
        rows.append(dict(event=label, group="55+ minus under-55", pct_change=100 * (np.exp(b) - 1),
                         placebo_sd_pct=100 * pl.std(), placebo_p=(np.abs(pl) >= abs(b)).mean(), n_placebos=len(pl)))
        print(f"{label:40s} 55+ minus <55 {100*(np.exp(b)-1):+6.2f}%  placebo SD {100*pl.std():.2f}%  p={(np.abs(pl) >= abs(b)).mean():.2f}")

    pd.DataFrame(rows).to_csv("results/suicide_estimates.csv", index=False)
    panel().to_csv("results/suicides_monthly.csv", index=False)
