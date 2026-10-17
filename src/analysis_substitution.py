"""Did attention move to other comedy when shows went dark?

Google Trends weekly US interest (one query per set, so terms share a scale), 2022-2025.
(1) 2023 strike: for each term, log interest in strike weeks (May 2 - Oct 2, 2023) vs the same
    weeks of 2022 and 2024, net of each year's level: log y = beta * strike + year FE + week FE.
    Placebo: a fake strike placed in 2022 (compared with 2024) and in 2024 (compared with 2022).
(2) South Park: log interest ~ beta * (new South Park releases that week) + year FE + week FE.
    A substitute should show a NEGATIVE beta (more interest when South Park is off).
"""
import numpy as np, pandas as pd, pyfixest as pf
from analysis_southpark import ep as sp_dates

def load(name):
    x = pd.read_csv(f"data/trends/{name}_weekly.csv", parse_dates=["date"]).melt("date", var_name="term", value_name="v")
    x["y"] = np.log(x.v.clip(lower=1))
    x["year"], x["woy"] = x.date.dt.year, x.date.dt.isocalendar().week.clip(upper=52).astype(int)
    return x

rows = []
ln = load("latenight_subs")
for term, g in ln.groupby("term"):
    def b(treat_year, years, lo="05-02", hi="10-02"):
        x = g[g.year.isin(years)].copy()
        x["strike"] = ((x.year == treat_year) & (x.date >= f"{treat_year}-{lo}") & (x.date < f"{treat_year}-{hi}")).astype(int)
        return pf.feols("y ~ strike | year + woy", data=x, vcov="hetero").tidy().loc["strike"]
    t = b(2023, [2022, 2023, 2024])
    pl = [b(2022, [2022, 2024]).Estimate, b(2024, [2022, 2024]).Estimate]
    rows.append(dict(analysis="2023 strike", term=term, pct=100 * (np.exp(t.Estimate) - 1), se_log=t["Std. Error"], p=t["Pr(>|t|)"],
                     placebo_pct=", ".join(f"{100*(np.exp(v)-1):+.0f}%" for v in pl)))
sp = load("southpark_subs")
wk = sp_dates.dt.to_period("W-SAT").value_counts()
sp["new"] = sp.date.dt.to_period("W-SAT").map(wk).fillna(0)
for term, g in sp.groupby("term"):
    t = pf.feols("y ~ new | year + woy", data=g, vcov="hetero").tidy().loc["new"]
    rows.append(dict(analysis="South Park new release (per episode in week)", term=term, pct=100 * (np.exp(t.Estimate) - 1),
                     se_log=t["Std. Error"], p=t["Pr(>|t|)"], placebo_pct=""))
    g2 = g[g.date < "2025-07-01"].copy()
    g2["gap"] = (g2.date >= "2023-04-01").astype(int)
    t = pf.feols("y ~ gap | woy", data=g2, vcov="hetero").tidy().loc["gap"]
    rows.append(dict(analysis="South Park 2023-25 gap vs Jan 2022-Mar 2023", term=term, pct=100 * (np.exp(t.Estimate) - 1),
                     se_log=t["Std. Error"], p=t["Pr(>|t|)"], placebo_pct=""))
out = pd.DataFrame(rows)
out.to_csv("results/substitution_trends.csv", index=False)
print(out.round(3).to_string(index=False))
