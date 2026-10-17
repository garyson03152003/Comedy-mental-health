"""Hiatus exposure weighted by each age group's propensity to watch TV (ATUS), on top of show popularity.

BRFSS:  dose_age = age TV propensity x state show-popularity dose (analysis_popularity.add_dose).
        (A) y ~ dose_age                         fully weighted effect
        (B) y ~ dose + dose x (agep - 1)         do heavier-viewing ages react more?  Age-specific
            season and week fixed effects absorb age-specific seasonality.
Suicides (national, month x ten-year age group, 15+):
        dose_at = age propensity x national popularity-weighted dark share.
        (A) FE age x year + age x calendar month
        (B) adds month fixed effects: identified only from differences between ages within a month.
"""
import numpy as np, pandas as pd, pyfixest as pf
import analysis_strikes as A, analysis_popularity as P
from analysis_suicide import d as deaths, EVENT_YEARS

prop = pd.read_csv("results/atus_tv_by_age.csv")
def agep(period, scheme):
    x = prop[(prop.period == period) & (prop.scheme == scheme)]
    return dict(zip(x.group if scheme == "wonder_age" else x.group.astype(int), x.propensity))

rows = []
def rec(label, y, tidy, term):
    t = tidy.loc[term]
    rows.append(dict(analysis=label, outcome=y, term=term, est=t.Estimate, se=t["Std. Error"], p=t["Pr(>|t|)"]))
    print(f"{label:44s} {y:9s} {term:10s} {t.Estimate:+.3f} (se {t['Std. Error']:.3f}, p={t['Pr(>|t|)']:.2f})")

def prep(s, period):
    s = s.copy()
    s["agep"] = s.agegrp.astype(int).map(agep(period, "brfss_ageg5yr"))
    s["agep_c"] = s.agep - np.average(s.agep, weights=s.weight)
    s["dose_age"] = s.dose * s.agep
    s["dose_x_age"] = s.dose * s.agep_c
    s["age_season"] = s.agegrp.astype(int).astype(str) + "_" + s.season.astype(str)
    s["age_week"] = s.agegrp.astype(int).astype(str) + "_" + s.week.astype(str)
    return s

def fit(s, y, rhs, fe):
    return pf.feols(f"{y} ~ {rhs} + sex_female + C(educ) | {fe}", data=s.dropna(subset=[y]),
                    weights="weight", vcov={"CRV1": "state"}).tidy()

FE_A = "season + week + state_season + C(agegrp)"
FE_B = "age_season + age_week + state_season"

if __name__ == "__main__":
    cases = [("2023 strike", "wga2023", "wga2023_latenight", 1, [2022, 2023, 2024], 2023, "pre2023", ["menthlth", "fmd"], 0),
             ("2023 strike (vs 2024-25)", "wga2023", "wga2023_latenight", 1, [2023, 2024, 2025], 2023, "pre2023", ["lonely"], 0),
             ("2007-08 strike", "wga2007", "wga2007_latenight", 7, [2006, 2007, 2008], 2007, "pre2007", ["menthlth", "fmd"], 0),
             ("PLACEBO 2022 (vs 2024)", "wga2023", "wga2023_latenight", 1, [2022, 2024], 2022, "pre2023", ["menthlth"], -1),
             ("PLACEBO 2024 (vs 2022)", "wga2023", "wga2023_latenight", 1, [2022, 2024], 2024, "pre2023", ["menthlth"], 1),
             ("PLACEBO 2024 (vs 2025)", "wga2023", "wga2023_latenight", 1, [2024, 2025], 2024, "pre2023", ["lonely"], 1),
             ("PLACEBO 2025 (vs 2024)", "wga2023", "wga2023_latenight", 1, [2024, 2025], 2025, "pre2023", ["lonely"], 2)]
    for label, strike, ev, m0, seasons, treated, period, ys, shift in cases:
        s = P.add_dose(A.setup(A.d, ev, m0, seasons, treated, shift_years=shift), strike, shift)
        if m0 == 7:
            s = s[s.week <= 47]
        s = prep(s, period)
        for y in ys:
            rec(label + ": age+popularity weighted", y, fit(s, y, "dose_age", FE_A), "dose_age")
            rec(label + ": extra per +1 age propensity", y, fit(s, y, "dose + dose_x_age", FE_B), "dose_x_age")
    pd.DataFrame(rows).to_csv("results/age_weighted_estimates.csv", index=False)

    # ---------------- suicides: month x age-group panel ----------------
    x = deaths[deaths.age.isin(prop[prop.scheme == "wonder_age"].group.unique())]
    p = x.groupby(["month", "age"], as_index=False).deaths.sum()
    p = p[p.deaths > 0]
    p["y"] = np.log(p.deaths / p.month.dt.days_in_month)
    p["year"], p["moy"] = p.month.dt.year, p.month.dt.month
    p["age_year"], p["age_moy"] = p.age + p.year.astype(str), p.age + p.moy.astype(str)
    p["mkey"] = p.month.astype(str)
    ap = np.where(p.month < "2015-01-01", p.age.map(agep("pre2007", "wonder_age")), p.age.map(agep("pre2023", "wonder_age")))
    scale = P.nat_dose(pd.Series(sorted(p.month.unique()))).max()
    def run(shift, fe):
        dose = P.nat_dose(p.month.reset_index(drop=True), shift) / scale * ap
        return pf.feols(f"y ~ dose | {fe}", data=p.assign(dose=dose)).coef()["dose"]
    srows = []
    for name, fe in [("A: age x year + age x month-of-year FE", "age_year + age_moy"),
                     ("B: + month FE (within-month, across ages)", "age_year + age_moy + mkey")]:
        b = run(0, fe)
        pl = []
        for k in range(-200, 220):
            hit = {(pd.Timestamp(t) + pd.DateOffset(months=k)).year for sh in P.DARK.values() for w in sh.values() for t in w}
            if k == 0 or hit & (EVENT_YEARS | {2020}) or min(hit) < 1999 or max(hit) > 2025:
                continue
            pl.append(run(k, fe))
        pl = np.array(pl)
        srows.append(dict(model=name, pct_change_per_unit=100 * (np.exp(b) - 1), placebo_sd_pct=100 * pl.std(),
                          placebo_p=(np.abs(pl) >= abs(b)).mean(), n_placebos=len(pl)))
        print(f"suicides {name:44s} {100*(np.exp(b)-1):+.2f}% per unit dose  placebo SD {100*pl.std():.2f}%  "
              f"p={(np.abs(pl) >= abs(b)).mean():.2f}")
    pd.DataFrame(srows).to_csv("results/age_weighted_suicides.csv", index=False)
