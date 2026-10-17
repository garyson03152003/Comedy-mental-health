"""Did the 2007-08 and 2023 writers' strikes (late-night/comedy TV hiatus) move mental health?

Design: BRFSS respondents report mentally unhealthy days in the past 30 days. For each
interview date we compute the share of that 30-day recall window that fell inside the
hiatus. Strike-season interviews are compared with the same calendar weeks in adjacent
(non-strike) seasons, with season, week-of-season and state-by-season fixed effects.
"""
import numpy as np, pandas as pd, pyfixest as pf
from events import window

d = pd.read_parquet("data/interim/brfss.parquet")
d["older"] = (d.agegrp >= 7).astype(float).where(d.agegrp.notna())       # 50+
d["older_alone"] = d.older * d.lives_alone

def exposure(dates, start, end):
    """Share of the 30-day recall window [t-29, t] that overlaps the hiatus [start, end)."""
    lo = np.maximum((dates - pd.Timedelta(days=29)).values, np.datetime64(start))
    hi = np.minimum((dates + pd.Timedelta(days=1)).values, np.datetime64(end))
    return np.clip((hi - lo) / np.timedelta64(1, "D"), 0, 30) / 30

def setup(df, event, season_start_md, seasons, treated, shift_years=0):
    """Restrict to a season-aligned sample and add exposure + fixed-effect keys.

    shift_years moves the hiatus window (for placebo tests in non-strike years)."""
    start, end = (t + pd.DateOffset(years=shift_years) for t in window(event))
    s = df.copy()
    # season label = calendar year in which the season starts
    shift = s.date - pd.DateOffset(months=season_start_md - 1)
    s["season"] = shift.dt.year
    s = s[s.season.isin(seasons)].copy()
    s["week"] = ((s.date - pd.to_datetime(s.season.astype(str) + f"-{season_start_md:02d}-01")).dt.days // 7).clip(upper=51)
    s["treat"] = (s.season == treated).astype(int)
    s["exp"] = np.where(s.treat == 1, exposure(s.date, start, end), 0.0)
    s["state_season"] = s.state.astype(str) + "_" + s.season.astype(str)
    return s.dropna(subset=["state", "agegrp", "sex_female"])

CTRL = "C(agegrp) + sex_female + C(educ)"

def fit(s, y, extra="", fe="season + week + state_season"):
    m = pf.feols(f"{y} ~ exp {extra} + {CTRL} | {fe}", data=s.dropna(subset=[y]),
                 weights="weight", vcov={"CRV1": "state"})
    return m

rows = []
def record(label, m, y, s, coef="exp"):
    t = m.tidy().loc[coef]
    base = np.average(s[y].dropna(), weights=s.loc[s[y].notna(), "weight"])
    rows.append(dict(analysis=label, outcome=y, term=coef, est=t.Estimate, se=t["Std. Error"],
                     p=t["Pr(>|t|)"], baseline_mean=base, n=m._N))
    print(f"{label:40s} {y:10s} {coef:22s} {t.Estimate:+.3f} (se {t['Std. Error']:.3f}, p={t['Pr(>|t|)']:.3f}) base={base:.3f}")

# ---------------- 2023 WGA strike (late night dark May 2 - Oct 2, 2023) ----------------
s23 = setup(d, "wga2023_latenight", 1, [2022, 2023, 2024], 2023)
for y in ["menthlth", "fmd"]:
    record("2023 strike: all adults", fit(s23, y), y, s23)
s23l = setup(d, "wga2023_latenight", 1, [2023, 2024, 2025], 2023)
record("2023 strike: all adults (vs 2024-25)", fit(s23l, "lonely"), "lonely", s23l)

# heterogeneity: 50+ living alone (heaviest late-night / companionship viewers)
for lab, s_, ys in [("2023 strike", s23, ["menthlth", "fmd"]), ("2023 strike (vs 2024-25)", s23l, ["lonely"])]:
    s_ = s_.dropna(subset=["older_alone"]).copy()
    s_["exp_x_oa"] = s_.exp * s_.older_alone
    s_["oa_season"] = s_.older_alone.astype(int).astype(str) + s_.season.astype(str)
    s_["oa_week"] = s_.older_alone.astype(int).astype(str) + "_" + s_.week.astype(str)
    for y in ys:
        m = fit(s_, y, "+ exp_x_oa", fe="oa_season + oa_week + state_season")
        record(lab + ": extra effect 50+ alone", m, y, s_, "exp_x_oa")

# placebos: pretend the strike happened in a non-strike year, excluding the real 2023
sp = setup(d, "wga2023_latenight", 1, [2022, 2024], 2022, shift_years=-1)
record("PLACEBO 2022 'strike' (vs 2024)", fit(sp, "menthlth"), "menthlth", sp)
sp = setup(d, "wga2023_latenight", 1, [2022, 2024], 2024, shift_years=1)
record("PLACEBO 2024 'strike' (vs 2022)", fit(sp, "menthlth"), "menthlth", sp)
spl = setup(d, "wga2023_latenight", 1, [2024, 2025], 2024, shift_years=1)
record("PLACEBO 2024 'strike' (vs 2025)", fit(spl, "lonely"), "lonely", spl)
spl = setup(d, "wga2023_latenight", 1, [2024, 2025], 2025, shift_years=2)
record("PLACEBO 2025 'strike' (vs 2024)", fit(spl, "lonely"), "lonely", spl)

# leave-one-comparison-year-out for the 2023 estimates
for comp in [[2022], [2024]]:
    s_ = setup(d, "wga2023_latenight", 1, [2023] + comp, 2023)
    record(f"2023 strike vs {comp[0]} only", fit(s_, "menthlth"), "menthlth", s_)
for comp in [[2024], [2025]]:
    s_ = setup(d, "wga2023_latenight", 1, [2023] + comp, 2023)
    record(f"2023 strike vs {comp[0]} only", fit(s_, "lonely"), "lonely", s_)

# ---------------- 2007-08 WGA strike (Nov 5 2007 - ~Mar 2008 for scripted TV) ----------------
s07 = setup(d, "wga2007_scripted", 7, [2006, 2007, 2008], 2007)
s07 = s07[s07.week <= 47]  # July - May
for y in ["menthlth", "fmd"]:
    record("2007-08 strike: all adults", fit(s07, y), y, s07)
s07o = s07.dropna(subset=["older_alone"]).copy()
s07o["exp_x_oa"] = s07o.exp * s07o.older_alone
s07o["oa_season"] = s07o.older_alone.astype(int).astype(str) + s07o.season.astype(str)
s07o["oa_week"] = s07o.older_alone.astype(int).astype(str) + "_" + s07o.week.astype(str)
record("2007-08 strike: extra effect 50+ alone", fit(s07o, "menthlth", "+ exp_x_oa",
       fe="oa_season + oa_week + state_season"), "menthlth", s07o, "exp_x_oa")

pd.DataFrame(rows).to_csv("results/strike_estimates.csv", index=False)

# ---------------- monthly event study, 2023 vs 2022/2024 ----------------
s23["month"] = s23.date.dt.month
es = pf.feols(f"menthlth ~ i(month, treat, ref=4) + {CTRL} | season + month + state_season",
              data=s23, weights="weight", vcov={"CRV1": "state"})
es.tidy().filter(like="month", axis=0).to_csv("results/event_study_2023_menthlth.csv")
s23l["month"] = s23l.date.dt.month
esl = pf.feols(f"lonely ~ i(month, treat, ref=4) + {CTRL} | season + month + state_season",
               data=s23l.dropna(subset=["lonely"]), weights="weight", vcov={"CRV1": "state"})
esl.tidy().filter(like="month", axis=0).to_csv("results/event_study_2023_lonely.csv")
print(es.tidy().filter(like="month", axis=0)[["Estimate", "Std. Error"]])
