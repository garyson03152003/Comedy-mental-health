"""TV-watching propensity by age from the American Time Use Survey (CRAN `atus` package, 2003-2016).

The abridged files have daily minutes per activity but no clock times, so this is *total* TV time
(codes 120303 TV/movies + 120304 religious TV), not late-night TV specifically. Propensity = weighted
mean minutes in an age group / population mean, so the population average is 1.
Periods: 2003-06 (before the 2007-08 strike) and 2013-16 (latest available, used for 2023).
"""
import numpy as np, pandas as pd, pyreadr

R = "data/raw/atus_pkg/atus/data/{}.rda"
act, resp, cps = (list(pyreadr.read_r(R.format(f)).values())[0] for f in ("atusact", "atusresp", "atuscps"))
tv = act[act.tiercode.isin([120303, 120304])].groupby("tucaseid").dur.sum()
d = resp[["tucaseid", "tuyear", "wt"]].merge(cps[["tucaseid", "age"]], on="tucaseid")
d["tv"] = d.tucaseid.map(tv).fillna(0)

# BRFSS _AGEG5YR codes: 1=18-24, 2=25-29, ..., 12=75-79, 13=80+
brfss = pd.cut(d.age, [17, 24, 29, 34, 39, 44, 49, 54, 59, 64, 69, 74, 79, 200], labels=range(1, 14))
# CDC WONDER ten-year groups
wonder = pd.cut(d.age, [14, 24, 34, 44, 54, 64, 74, 84, 200],
                labels=["15-24 years", "25-34 years", "35-44 years", "45-54 years", "55-64 years",
                        "65-74 years", "75-84 years", "85+ years"])
rows = []
for period, years in [("pre2007", range(2003, 2007)), ("pre2023", range(2013, 2017))]:
    x = d[d.tuyear.isin(years)]
    for scheme, groups in [("brfss_ageg5yr", brfss), ("wonder_age", wonder)]:
        g = groups[x.index]
        mean_all = np.average(x.tv[g.notna()], weights=x.wt[g.notna()])
        for k, xx in x.groupby(g, observed=True):
            m = np.average(xx.tv, weights=xx.wt)
            rows.append(dict(period=period, scheme=scheme, group=str(k), tv_minutes=m,
                             propensity=m / mean_all, n=len(xx)))
out = pd.DataFrame(rows)
out.to_csv("results/atus_tv_by_age.csv", index=False)
print(out[out.scheme == "wonder_age"].pivot(index="group", columns="period", values=["tv_minutes", "propensity"]).round(2))
