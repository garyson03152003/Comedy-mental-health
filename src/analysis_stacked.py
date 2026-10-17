"""Stacked difference-in-differences across late-night shows that paused, ended or were replaced.

For each event e (data/show_events.csv) and age group g, intensity I_eg = (relative viewing rate of
the show's audience in g) - 1, from results/show_age_profiles.csv (calibrated to Nielsen median ages).
Treatment D_et = share of period t the show was gone (paused: until it returned; ended/replaced: from
the last episode on). Each event contributes its own window; the model is

    y_egt = beta * D_et * I_eg + event x group FE + event x period FE

so beta compares age groups that watched the show more vs less, within the same event and period.
beta = change in y for an age group that watched at twice the population rate while the show was gone.
Placebo: every event moved by +-1..3 years (same windows, same intensities).
"""
import sys
import numpy as np, pandas as pd, pyfixest as pf
from analysis_southpark import load
from analysis_suicide import share

EV = pd.read_csv("data/show_events.csv", parse_dates=["start", "end"])
PROF = pd.read_csv("results/show_age_profiles.csv")
EVENTS = EV.groupby("event").agg(type=("type", "first"), start=("start", "min"), end=("end", "max"),
                                 ongoing=("end", lambda s: s.isna().any())).reset_index()
WINDOW_MONTHS = 12

def intensity(scheme):
    p = PROF[PROF.scheme == scheme].copy()
    p["I"] = p.rate - 1
    return p.set_index(["event", "group"]).I

def gone(e, start, end, ongoing, t0, t1):
    """Share of [t0, t1) the show was gone; t0, t1 arrays of datetime64[D]."""
    stop = np.datetime64("2100-01-01") if ongoing else np.datetime64(end, "D")
    lo, hi = np.maximum(t0, np.datetime64(start, "D")), np.minimum(t1, stop)
    return np.clip((hi - lo).astype(int), 0, None) / (t1 - t0).astype(int)

# ---------------- suicides: month x ten-year age group ----------------
def suicide_panel():
    a = load("data/wonder/d76_month_sex_age.csv"); a = a[a.month < "2018-01-01"]
    b = load("data/wonder/d176_month_sex_age.csv"); b = b[~b.partial]
    s = pd.concat([a, b])
    s = s[(s.month < "2026-01-01")].groupby(["month", "age"], as_index=False).deaths.sum()
    s = s[~s.age.isin(["Not Stated", "5-14 years"])]
    s["y"] = np.log(s.deaths / s.month.dt.days_in_month)
    return s

def stack_suicides(s, I, shift_years=0, types=None):
    parts = []
    for e in EVENTS.itertuples():
        if types and e.type not in types: continue
        st = e.start + pd.DateOffset(years=shift_years)
        en = e.end + pd.DateOffset(years=shift_years) if pd.notna(e.end) else e.end
        lo, hi = st - pd.DateOffset(months=WINDOW_MONTHS), st + pd.DateOffset(months=WINDOW_MONTHS)
        x = s[(s.month >= lo) & (s.month < hi)].copy()
        if x.month.nunique() < 2 * WINDOW_MONTHS - 1: continue  # window must lie inside the data
        t0 = x.month.values.astype("datetime64[D]")
        t1 = (x.month + pd.offsets.MonthBegin(1)).values.astype("datetime64[D]")
        x["D"] = gone(e.event, st, en, e.ongoing, t0, t1)
        x["I"] = [I.get((e.event, g), np.nan) for g in x.age]
        x["ev"], x["eg"], x["et"] = e.event, e.event + x.age, e.event + x.month.astype(str)
        parts.append(x)
    x = pd.concat(parts).dropna(subset=["I"])
    x["DI"] = x.D * x.I
    return x

def est(x, y="y", w=None, vc=None):
    m = pf.feols(f"{y} ~ DI | eg + et", data=x, weights=w, vcov=vc or {"CRV1": "eg"})
    return m

if __name__ == "__main__" and "--brfss" not in sys.argv:
    rows = []
    s, I = suicide_panel(), intensity("wonder")
    for label, types in [("all events", None), ("paused", ["paused"]), ("ended or replaced", ["ended", "replaced"])]:
        x = stack_suicides(s, I, types=types)
        t = est(x).tidy().loc["DI"]
        pl = np.array([est(stack_suicides(s, I, k, types)).coef()["DI"] for k in (-3, -2, -1, 1, 2, 3)])
        rows.append(dict(outcome="suicides (log)", events=label, n_events=x.ev.nunique(), est=t.Estimate,
                         se=t["Std. Error"], p=t["Pr(>|t|)"], placebo_sd=pl.std(), placebo_p=(np.abs(pl) >= abs(t.Estimate)).mean()))
        print(f"suicides  {label:18s} ({x.ev.nunique()} events): {100*t.Estimate:+.2f}% per +1 viewing rate "
              f"(se {100*t['Std. Error']:.2f}, p={t['Pr(>|t|)']:.2f}); placebo SD {100*pl.std():.2f}%, "
              f"placebo p={(np.abs(pl) >= abs(t.Estimate)).mean():.2f}")
    # per-event estimates
    for e in EVENTS.event:
        x = stack_suicides(s, I)
        x = x[x.ev == e]
        if x.empty or x.DI.abs().sum() == 0: continue
        t = est(x).tidy().loc["DI"]
        rows.append(dict(outcome="suicides (log)", events=e, n_events=1, est=t.Estimate, se=t["Std. Error"], p=t["Pr(>|t|)"]))
        print(f"  {e:26s} {100*t.Estimate:+6.2f}% (se {100*t['Std. Error']:.2f})")
    pd.DataFrame(rows).to_csv("results/stacked_suicides.csv", index=False)

# ---------------- BRFSS: interview date x age group (stacked, +-6 months) ----------------
def brfss_stack(b, I, shift_years=0, types=None, months=6):
    parts = []
    for e in EVENTS.itertuples():
        if types and e.type not in types: continue
        st = e.start + pd.DateOffset(years=shift_years)
        en = e.end + pd.DateOffset(years=shift_years) if pd.notna(e.end) else e.end
        lo, hi = st - pd.DateOffset(months=months), st + pd.DateOffset(months=months)
        x = b[(b.date >= lo) & (b.date < hi)]
        if x.empty or x.date.min() > lo + pd.Timedelta(days=31) or x.date.max() < hi - pd.Timedelta(days=31):
            continue  # window not covered by downloaded BRFSS years
        t = x.date.values.astype("datetime64[D]")
        D = gone(e.event, st, en, e.ongoing, t - np.timedelta64(29, "D"), t + np.timedelta64(1, "D"))
        Ie = x.agegrp.astype(int).astype(str).map(I.xs(e.event, level="event")).values
        parts.append(pd.DataFrame({"ev": e.event, "DI": D * Ie, "agegrp": x.agegrp.values, "date": x.date.values,
                                   "state": x.state.values, "sex": x.sex_female.values, "educ": x.educ.fillna(-1).values,
                                   "w": x.weight.values, "menthlth": x.menthlth.values, "fmd": x.fmd.values,
                                   "lonely": x.lonely.values}))
    x = pd.concat(parts, ignore_index=True)
    code = lambda *k: pd.factorize(pd.MultiIndex.from_arrays(k))[0].astype("int32")
    x["eg"], x["ed"], x["es"] = code(x.ev, x.agegrp), code(x.ev, x.date), code(x.ev, x.state)
    x["sx"] = code(x.sex, x.educ)
    return x

def brfss_est(x, y):
    return pf.feols(f"{y} ~ DI | eg + ed + es + sx", data=x.dropna(subset=[y]), weights="w", vcov={"CRV1": "state"})

if __name__ == "__main__" and "--brfss" in sys.argv:
    cols = ["date", "state", "agegrp", "sex_female", "educ", "weight", "menthlth", "fmd", "lonely"]
    b = pd.read_parquet("data/interim/brfss.parquet", columns=cols).dropna(subset=["agegrp", "state", "sex_female", "weight"])
    Ib = intensity("brfss")
    brows = []
    for label, types in [("all events", None), ("paused", ["paused"]), ("ended or replaced", ["ended", "replaced"])]:
        x = brfss_stack(b, Ib, types=types)
        for y in ["menthlth", "fmd"]:
            t = brfss_est(x, y).tidy().loc["DI"]
            pl = []
            for k in (-3, -2, -1, 1, 2, 3):
                try:
                    pl.append(brfss_est(brfss_stack(b, Ib, k, types), y).coef()["DI"])
                except ValueError:
                    pass  # no shifted window covered by the data
            pl = np.array(pl)
            brows.append(dict(outcome=y, events=label, n_events=x.ev.nunique(), est=t.Estimate, se=t["Std. Error"],
                              p=t["Pr(>|t|)"], placebo_sd=pl.std(), placebo_p=(np.abs(pl) >= abs(t.Estimate)).mean(),
                              n_placebos=len(pl)))
            print(f"BRFSS {y:9s} {label:18s} ({x.ev.nunique()} events): {t.Estimate:+.3f} per +1 viewing rate "
                  f"(se {t['Std. Error']:.3f}, p={t['Pr(>|t|)']:.2f}); placebo SD {pl.std():.3f} (n={len(pl)})")
    x = brfss_stack(b, Ib)
    for e in x.ev.unique():
        t = brfss_est(x[x.ev == e], "menthlth").tidy().loc["DI"]
        brows.append(dict(outcome="menthlth", events=e, n_events=1, est=t.Estimate, se=t["Std. Error"], p=t["Pr(>|t|)"]))
        print(f"  {e:26s} menthlth {t.Estimate:+.3f} (se {t['Std. Error']:.3f})")
    pd.DataFrame(brows).to_csv("results/stacked_brfss.csv", index=False)
