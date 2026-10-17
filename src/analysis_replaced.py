"""Comedy replaced by other programming.

(1) NBC Olympics: The Tonight Show is preempted by Games coverage (~2.5 weeks every two years).
    Same stacked DiD as analysis_stacked.py: age groups that watch the Tonight Show more vs less,
    same event and period. 2010 and 2014 are left out because they overlap the Conan exit and
    Leno's final show. The Olympics themselves skew older too, so this is the net effect of
    "comedy swapped for sports", not of losing TV.
(2) CBS 12:37am: After Midnight's last episode (June 12, 2025); the slot went to non-comedy/repeat
    programming. No age data for its audience, so this uses the population-level design of
    analysis_strikes.py (2025 vs the same weeks of 2023-24).
"""
import sys
import numpy as np, pandas as pd, pyfixest as pf
import analysis_stacked as S

S.EVENTS = (pd.read_csv("data/replacement_events.csv", parse_dates=["start", "end"])
            .groupby("event").agg(type=("type", "first"), start=("start", "min"), end=("end", "max"),
                                  ongoing=("end", lambda s: s.isna().any())).reset_index())
S.PROF = pd.read_csv("results/replacement_age_profiles.csv")
rows = []

def run(label, stack, fit, data, I, outcome, scale=1):
    x = stack(data, I)
    t = fit(x).tidy().loc["DI"]
    pl = []
    for k in (-3, -2, -1, 1, 2, 3):   # every event moved by whole years (same season)
        try:
            pl.append(fit(stack(data, I, k)).coef()["DI"])
        except ValueError:
            pass
    pl = np.array(pl)
    rows.append(dict(analysis=label, outcome=outcome, n_events=x.ev.nunique(), est=t.Estimate, se=t["Std. Error"],
                     p=t["Pr(>|t|)"], placebo_sd=pl.std(), placebo_p=(np.abs(pl) >= abs(t.Estimate)).mean()))
    print(f"{label:44s} {outcome:9s} ({x.ev.nunique()} events) {scale*t.Estimate:+.3f} (se {scale*t['Std. Error']:.3f}, "
          f"p={t['Pr(>|t|)']:.2f}); placebo SD {scale*pl.std():.3f}")
    return x

if "--brfss" not in sys.argv:
    s, I = S.suicide_panel(), S.intensity("wonder")
    run("Olympics replace Tonight Show: suicides (%)", S.stack_suicides, S.est, s, I, "suicides", 100)
    keep = S.EVENTS.event != "olympics2021"
    full = S.EVENTS
    S.EVENTS = full[keep]
    run("  ...excluding Tokyo 2021 (COVID)", S.stack_suicides, S.est, s, I, "suicides", 100)
    S.EVENTS = full
    pd.DataFrame(rows).to_csv("results/replaced_suicides.csv", index=False)
else:
    import analysis_strikes as A
    from events import EVENTS
    cols = ["date", "state", "agegrp", "sex_female", "educ", "weight", "menthlth", "fmd", "lonely"]
    b = pd.read_parquet("data/interim/brfss.parquet", columns=cols).dropna(subset=["agegrp", "state", "sex_female", "weight"])
    Ib = S.intensity("brfss")
    for y in ["menthlth", "fmd"]:
        run("Olympics replace Tonight Show: BRFSS", lambda d, I, k=0: S.brfss_stack(d, I, k), lambda x: S.brfss_est(x, y), b, Ib, y)
    full = S.EVENTS
    S.EVENTS = full[full.event != "olympics2021"]
    run("  ...excluding Tokyo 2021 (COVID)", lambda d, I, k=0: S.brfss_stack(d, I, k), lambda x: S.brfss_est(x, "menthlth"), b, Ib, "menthlth")
    S.EVENTS = full
    x = S.brfss_stack(b, Ib)
    for e in x.ev.unique():
        t = S.brfss_est(x[x.ev == e], "menthlth").tidy().loc["DI"]
        rows.append(dict(analysis=e, outcome="menthlth", n_events=1, est=t.Estimate, se=t["Std. Error"], p=t["Pr(>|t|)"]))
        print(f"  {e:14s} menthlth {t.Estimate:+.3f} (se {t['Std. Error']:.3f})")
    del b, x
    # (2) After Midnight ends, June 12 2025 -> population-level, 2025 vs same weeks 2023-24
    EVENTS["aftermidnight2025"] = ("2025-06-13", "2026-01-01")
    for y, seasons in [("menthlth", [2023, 2024, 2025]), ("fmd", [2023, 2024, 2025]), ("lonely", [2023, 2024, 2025])]:
        s_ = A.setup(A.d, "aftermidnight2025", 1, seasons, 2025)
        m = A.fit(s_, y)
        t = m.tidy().loc["exp"]
        pl = [A.fit(A.setup(A.d, "aftermidnight2025", 1, seasons, yr, shift_years=yr - 2025), y).coef()["exp"]
              for yr in (2023, 2024)]
        rows.append(dict(analysis="After Midnight ends (CBS 12:37 slot), 2025 vs 2023-24", outcome=y, n_events=1,
                         est=t.Estimate, se=t["Std. Error"], p=t["Pr(>|t|)"], placebo_sd=np.std(pl), placebo_p=np.nan))
        print(f"After Midnight ends: {y:9s} {t.Estimate:+.3f} (se {t['Std. Error']:.3f}, p={t['Pr(>|t|)']:.2f}); "
              f"fake 2023/2024 endings: {', '.join(f'{v:+.3f}' for v in pl)}")
    pd.DataFrame(rows).to_csv("results/replaced_brfss.csv", index=False)
