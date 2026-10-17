"""South Park on/off air and the mental health of its core audience (men 18-34).

Exposure = number of new South Park releases (Comedy Central episodes + significant specials +
Paramount+ specials) in a month (suicides) or in the respondent's 30-day recall window (BRFSS).
South Park's schedule shifts a lot between years (e.g. no regular season Apr 2023 - Jul 2025), and
month-of-year fixed effects remove its usual spring/fall rhythm, so identification comes from those
year-to-year schedule differences. Triple differences compare young men with everyone else in the same month/day.

Placebos: the whole episode calendar shifted by whole years (another year's schedule, same seasonality).
"""
import re
import numpy as np, pandas as pd, pyfixest as pf
import analysis_strikes as A

ep = pd.read_csv("data/southpark_episodes.csv", parse_dates=["date"])
ep = ep[ep.type != "insignificant_special"].date

def monthly(dates, months):
    c = dates.dt.to_period("M").value_counts()
    return months.dt.to_period("M").map(c).fillna(0).values

def window_count(dates, t):
    """New releases in [t-29, t] for each interview date t."""
    e = np.sort(dates.values.astype("datetime64[D]"))
    t = t.values.astype("datetime64[D]")
    return np.searchsorted(e, t, side="right") - np.searchsorted(e, t - np.timedelta64(29, "D"), side="left")

shift = lambda years: ep + pd.DateOffset(years=years)

# ---------------- suicides: month x sex x ten-year age ----------------
def load(path):
    raw = pd.read_csv(path, dtype=str).fillna("")
    out, m, s = [], None, None
    for r in raw.itertuples(index=False):
        c = [x for x in r if x != ""]
        if re.match(r"^[A-Z][a-z]{2}\.?,? \d{4}", c[0]): m, c = c[0], c[1:]
        if c[0] in ("Female", "Male"): s, c = c[0], c[1:]
        out.append((m, s, c[0], c[1]))
    d = pd.DataFrame(out, columns=["label", "sex", "age", "deaths"])
    d["month"] = pd.to_datetime(d.label.str.extract(r"^(\w+)\.?,? (\d{4})").agg(" ".join, axis=1), format="%b %Y")
    d["partial"] = d.label.str.contains("partial")
    d["deaths"] = pd.to_numeric(d.deaths.str.replace(",", ""), errors="coerce")
    return d

if __name__ == "__main__":
    a = load("data/wonder/d76_month_sex_age.csv"); a = a[a.month < "2018-01-01"]
    b = load("data/wonder/d176_month_sex_age.csv"); b = b[~b.partial]
    s = pd.concat([a, b])
    s = s[(s.month < "2026-01-01") & ~s.age.isin(["Not Stated", "5-14 years"]) & (s.deaths > 0)].copy()
    s["g"] = s.sex + "_" + s.age
    s["target"] = ((s.sex == "Male") & s.age.isin(["15-24 years", "25-34 years"])).astype(int)
    s["y"] = np.log(s.deaths / s.month.dt.days_in_month)
    s["year"], s["moy"], s["mkey"] = s.month.dt.year, s.month.dt.month, s.month.astype(str)
    s["g_year"], s["g_moy"] = s.g + s.year.astype(str), s.g + "_" + s.moy.astype(str)
    s = s[s.groupby("g").y.transform("size") == s.groupby("g").y.transform("size").max()]  # balanced groups

    tm = s[s.target == 1].groupby("month", as_index=False).deaths.sum()
    tm["y"] = np.log(tm.deaths / tm.month.dt.days_in_month)
    tm["year"], tm["moy"] = tm.month.dt.year, tm.month.dt.month

    rows = []
    def go(label, fit_fn):
        b0 = fit_fn(ep)
        pl = np.array([fit_fn(shift(k)) for k in range(-12, 13) if k != 0])
        rows.append(dict(analysis=label, est_pct_per_episode=100 * b0, placebo_sd=100 * pl.std(),
                         placebo_p=(np.abs(pl) >= abs(b0)).mean(), n_placebos=len(pl)))
        print(f"{label:58s} {100*b0:+.2f}% per new episode  placebo SD {100*pl.std():.2f}  p={(np.abs(pl) >= abs(b0)).mean():.2f}")

    go("suicides, men 15-34 (year + calendar-month FE)",
       lambda e: pf.feols("y ~ n | year + moy", data=tm.assign(n=monthly(e, tm.month))).coef()["n"])
    go("suicides, men 15-34 vs all other sex-age groups, same month",
       lambda e: pf.feols("y ~ nt | g_year + g_moy + mkey",
                          data=s.assign(nt=monthly(e, s.month) * s.target)).coef()["nt"])
    # the long 2023-25 gap specifically: Apr 2023 - Jun 2025 with no regular season
    s["gap"] = ((s.month >= "2023-04-01") & (s.month < "2025-07-01")).astype(int) * s.target
    t = pf.feols("y ~ gap | g_year + g_moy + mkey", data=s[s.year >= 2015], vcov={"CRV1": "g"}).tidy().loc["gap"]
    rows.append(dict(analysis="suicides, men 15-34 vs others during Apr 2023-Jun 2025 gap (2015+)",
                     est_pct_per_episode=100 * t.Estimate, placebo_sd=np.nan, placebo_p=t["Pr(>|t|)"], n_placebos=0))
    print(f"suicides, men 15-34 relative change during 2023-25 gap: {100*t.Estimate:+.2f}% (se {100*t['Std. Error']:.2f}, p={t['Pr(>|t|)']:.2f})")

    # ---------------- BRFSS: young men vs everyone else, same interview day ----------------
    cols = ["date", "state", "agegrp", "educ", "sex_female", "weight", "menthlth", "fmd", "lonely"]
    d = A.d.loc[A.d.date.dt.year.isin([2006, 2007, 2008, 2009, 2022, 2023, 2024, 2025]), cols]
    d = d.dropna(subset=["agegrp", "sex_female", "state", "weight"]).reset_index(drop=True)
    del A.d
    d["target"] = ((d.sex_female == 0) & (d.agegrp <= 3)).astype("int8")   # men 18-34
    year, woy = d.date.dt.year, d.date.dt.isocalendar().week.clip(upper=52).astype(int)
    code = lambda *k: pd.factorize(pd.MultiIndex.from_arrays(k))[0].astype("int32")
    d["t_year"], d["t_week"] = code(d.target, year), code(d.target, woy)
    d["state_year"], d["dkey"] = code(d.state, year), code(d.date)
    d["age_educ"] = code(d.agegrp, d.educ.fillna(-1), d.sex_female)
    d["year"] = year
    for c in ["menthlth", "fmd", "lonely", "weight"]:
        d[c] = d[c].astype("float32")
    def brfss(y, e, data):
        x = data.assign(nt=window_count(e, data.date) * data.target).dropna(subset=[y])
        return pf.feols(f"{y} ~ nt | t_year + t_week + state_year + dkey + age_educ",
                        data=x, weights="weight", vcov={"CRV1": "state"})
    for y, data in [("menthlth", d), ("fmd", d), ("lonely", d[d.year >= 2023])]:
        m = brfss(y, ep, data); t = m.tidy().loc["nt"]
        pl = np.array([brfss(y, shift(k), data).coef()["nt"] for k in (-3, -2, -1, 1, 2, 3)])
        rows.append(dict(analysis=f"BRFSS {y}, men 18-34 vs others, per new episode in past 30 days",
                         est_pct_per_episode=t.Estimate, placebo_sd=pl.std(), placebo_p=(np.abs(pl) >= abs(t.Estimate)).mean(),
                         n_placebos=len(pl)))
        print(f"BRFSS {y:9s} men 18-34 vs others, per new episode: {t.Estimate:+.4f} (se {t['Std. Error']:.4f}, "
              f"p={t['Pr(>|t|)']:.2f}); placebo SD {pl.std():.4f}")
    pd.DataFrame(rows).to_csv("results/southpark_estimates.csv", index=False)
