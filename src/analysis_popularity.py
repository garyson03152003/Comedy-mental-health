"""Popularity-weighted hiatus exposure.

Instead of 'was late night off air' (0/1), each respondent's exposure is the pre-strike popularity
of each show that went dark *in their state* (Google Trends, 12 months before the strike),
times the share of their 30-day recall window that show was dark, summed over shows. Shows are
weighted by their national pre-strike search interest. Units: 1 = an average-popularity state with
every show dark for the full 30 days, so estimates are comparable to the unweighted ones.

  (A) y ~ dose                       popularity-weighted effect
  (B) y ~ exp + exp x (P_state - 1)  dose-response: do states that liked the shows more react more?
Placebos re-run (B) with fake strikes in non-strike years using the same state popularity.
Suicides (national) pool both strikes with dose = national pre-strike popularity of dark shows.
"""
import numpy as np, pandas as pd, pyfixest as pf
import analysis_strikes as A  # reuses setup(), exposure(), CTRL and the BRFSS frame
from analysis_suicide import panel, share, EVENT_YEARS

FIPS = dict(Alabama=1, Alaska=2, Arizona=4, Arkansas=5, California=6, Colorado=8, Connecticut=9, Delaware=10,
    **{"District of Columbia": 11}, Florida=12, Georgia=13, Hawaii=15, Idaho=16, Illinois=17, Indiana=18,
    Iowa=19, Kansas=20, Kentucky=21, Louisiana=22, Maine=23, Maryland=24, Massachusetts=25, Michigan=26,
    Minnesota=27, Mississippi=28, Missouri=29, Montana=30, Nebraska=31, Nevada=32, **{"New Hampshire": 33,
    "New Jersey": 34, "New Mexico": 35, "New York": 36, "North Carolina": 37, "North Dakota": 38}, Ohio=39,
    Oklahoma=40, Oregon=41, Pennsylvania=42, **{"Rhode Island": 44, "South Carolina": 45, "South Dakota": 46},
    Tennessee=47, Texas=48, Utah=49, Vermont=50, Virginia=51, Washington=53, **{"West Virginia": 54},
    Wisconsin=55, Wyoming=56)

# Dates each show was dark (last original episode -> first new episode).
DARK = {
    "wga2007": {"Jay Leno": ("2007-11-05", "2008-01-02"), "David Letterman": ("2007-11-05", "2008-01-02"),
                "Conan": ("2007-11-05", "2008-01-02"), "Jimmy Kimmel": ("2007-11-05", "2008-01-02"),
                "Daily Show": ("2007-11-05", "2008-01-07")},
    "wga2023": {"Jimmy Fallon": ("2023-05-02", "2023-10-02"), "Stephen Colbert": ("2023-05-02", "2023-10-02"),
                "Seth Meyers": ("2023-05-02", "2023-10-02"), "Jimmy Kimmel": ("2023-05-02", "2023-10-24"),
                "Daily Show": ("2023-05-02", "2023-10-16")},
}

def weights(strike):
    nat = pd.read_csv(f"data/trends/{strike}_national.csv", index_col=0)["interest"]
    st = pd.read_csv(f"data/trends/{strike}_states.csv", index_col=0)
    st.index = st.index.map(FIPS)
    st = st / st.mean()                      # each show: average state = 1
    return nat / nat.sum(), st               # national show weights sum to 1

def add_dose(s, strike, shift_years=0):
    w, st = weights(strike)
    s = s[s.state.isin(st.index)].copy()
    s["dose"], s["P"] = 0.0, 0.0
    for show, (a, b) in DARK[strike].items():
        a, b = (pd.Timestamp(x) + pd.DateOffset(years=shift_years) for x in (a, b))
        e = np.where(s.treat == 1, A.exposure(s.date, a, b), 0.0)
        pop = s.state.map(st[show]).values
        s["dose"] += w[show] * pop * e
        s["P"] += w[show] * pop
    s["P_c"] = s.P - np.average(s.P, weights=s.weight)
    s["exp_x_P"] = s.exp * s.P_c
    return s

def fit(s, y, rhs):
    return pf.feols(f"{y} ~ {rhs} + {A.CTRL} | season + week + state_season", data=s.dropna(subset=[y]),
                    weights="weight", vcov={"CRV1": "state"}).tidy()

rows = []
def rec(label, y, tidy, term):
    t = tidy.loc[term]
    rows.append(dict(analysis=label, outcome=y, term=term, est=t.Estimate, se=t["Std. Error"], p=t["Pr(>|t|)"]))
    print(f"{label:38s} {y:9s} {term:8s} {t.Estimate:+.3f} (se {t['Std. Error']:.3f}, p={t['Pr(>|t|)']:.2f})")

cases = [("2023 strike", "wga2023", "wga2023_latenight", 1, [2022, 2023, 2024], 2023, ["menthlth", "fmd"]),
         ("2023 strike (vs 2024-25)", "wga2023", "wga2023_latenight", 1, [2023, 2024, 2025], 2023, ["lonely"]),
         ("2007-08 strike (late night)", "wga2007", "wga2007_latenight", 7, [2006, 2007, 2008], 2007, ["menthlth", "fmd"])]
for label, strike, ev, m0, seasons, treated, ys in cases:
    s = add_dose(A.setup(A.d, ev, m0, seasons, treated), strike)
    if m0 == 7:
        s = s[s.week <= 47]
    print(f"  {label}: state popularity index P ranges {s.P.min():.2f}-{s.P.max():.2f}")
    for y in ys:
        rec(label + ": weighted", y, fit(s, y, "dose"), "dose")
        rec(label + ": dose-response", y, fit(s, y, "exp + exp_x_P"), "exp_x_P")

# placebo dose-response: fake strikes in non-strike years, same state popularity
for label, seasons, treated, shift, y in [("PLACEBO 2022 (vs 2024)", [2022, 2024], 2022, -1, "menthlth"),
                                          ("PLACEBO 2024 (vs 2022)", [2022, 2024], 2024, 1, "menthlth"),
                                          ("PLACEBO 2024 (vs 2025)", [2024, 2025], 2024, 1, "lonely"),
                                          ("PLACEBO 2025 (vs 2024)", [2024, 2025], 2025, 2, "lonely")]:
    s = add_dose(A.setup(A.d, "wga2023_latenight", 1, seasons, treated, shift_years=shift), "wga2023", shift)
    rec(label + ": weighted", y, fit(s, y, "dose"), "dose")
    rec(label + ": dose-response", y, fit(s, y, "exp + exp_x_P"), "exp_x_P")

pd.DataFrame(rows).to_csv("results/popularity_weighted_estimates.csv", index=False)

# ---- suicides: pool both strikes, dose = national pre-strike popularity of the dark shows ----
lr = pd.read_csv("data/trends/national_monthly_2004_2025.csv", index_col=0, parse_dates=True)
def nat_dose(months, shift_months=0):
    dose = np.zeros(len(months))
    for strike, shows in DARK.items():
        pre_end = pd.Timestamp(next(iter(shows.values()))[0])
        pre = lr[(lr.index >= pre_end - pd.DateOffset(years=1)) & (lr.index < pre_end)]
        for show, (a, b) in shows.items():
            a, b = (pd.Timestamp(x) + pd.DateOffset(months=shift_months) for x in (a, b))
            dose += pre[show].mean() * share(months, a, b)
    return dose
srows = []
for grp_name, grp in [("all ages", None), ("55+", True), ("under 55", False)]:
    p = panel(grp)
    scale = nat_dose(p.month).max()  # 1 = the most popular strike-month dose
    b = pf.feols("y ~ dose | year + moy", data=p.assign(dose=nat_dose(p.month) / scale)).coef()["dose"]
    pl = []
    for k in range(-200, 220):
        if k == 0: continue
        months_hit = {(pd.Timestamp(x) + pd.DateOffset(months=k)).year for sh in DARK.values() for w in sh.values() for x in w}
        if months_hit & (EVENT_YEARS | {2020}) or min(months_hit) < 1999 or max(months_hit) > 2025:
            continue
        pl.append(pf.feols("y ~ dose | year + moy", data=p.assign(dose=nat_dose(p.month, k) / scale)).coef()["dose"])
    pl = np.array(pl)
    srows.append(dict(group=grp_name, pct_change_at_peak_dose=100 * (np.exp(b) - 1), placebo_sd_pct=100 * pl.std(),
                      placebo_p=(np.abs(pl) >= abs(b)).mean(), n_placebos=len(pl)))
    print(f"suicides, popularity-weighted pooled  {grp_name:9s} {100*(np.exp(b)-1):+.2f}% at peak dose  "
          f"placebo SD {100*pl.std():.2f}%  p={(np.abs(pl) >= abs(b)).mean():.2f}  ({len(pl)} placebos)")
pd.DataFrame(srows).to_csv("results/popularity_weighted_suicides.csv", index=False)
