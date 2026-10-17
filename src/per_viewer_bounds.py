"""Turn population-level estimates into bounds on the effect per actual viewer.

If a share s of adults watch, a population effect b implies a per-viewer effect b / s (all of the
effect sits on viewers). For the dose-response designs, +1 "viewing rate" (age profile) or
+1 popularity index means roughly s more viewers per person, so the same b / s scaling applies.
Uncertainty uses the larger of the model SE and the placebo SD, since placebos showed that
clustered SEs understate year-to-year noise.

Audience: Q1 2023 nightly averages of about 2.8M (Colbert), 1.75M (Kimmel), 1.6M (Fallon), derived
from LateNighter's Q1 2024 report and its year-over-year changes, sum to about 6.2M, or 2.4% of
~262M adults. Regular viewers (any night in a month) are more, so bounds are also shown at 5% and 10%.
"""
import numpy as np, pandas as pd

S = [0.024, 0.05, 0.10]
rows = []
def add(label, outcome, unit, est, se, placebo_sd=np.nan, baseline=np.nan):
    se_eff = np.nanmax([se, placebo_sd])
    lo, hi = est - 1.96 * se_eff, est + 1.96 * se_eff
    r = dict(estimate=label, outcome=outcome, unit=unit, pop_est=est, pop_lo=lo, pop_hi=hi, baseline=baseline)
    for s in S:
        r[f"viewer_lo_{s:g}"], r[f"viewer_hi_{s:g}"] = lo / s, hi / s
    rows.append(r)

st = pd.read_csv("results/strike_estimates.csv").set_index(["analysis", "outcome"])
pl_days = st.loc[[("PLACEBO 2022 'strike' (vs 2024)", "menthlth"), ("PLACEBO 2024 'strike' (vs 2022)", "menthlth")], "est"]
pl_lone = st.loc[[("PLACEBO 2024 'strike' (vs 2025)", "lonely"), ("PLACEBO 2025 'strike' (vs 2024)", "lonely")], "est"]
r = st.loc[("2023 strike: all adults", "menthlth")]
add("2023 strike, all adults", "mentally unhealthy days (of 30)", "days", r.est, r.se, np.sqrt((pl_days ** 2).mean()), r.baseline_mean)
r = st.loc[("2023 strike: all adults", "fmd")]
add("2023 strike, all adults", "frequent mental distress", "share", r.est, r.se, np.nan, r.baseline_mean)
r = st.loc[("2023 strike: all adults (vs 2024-25)", "lonely")]
add("2023 strike, all adults", "lonely at least sometimes", "share", r.est, r.se, np.sqrt((pl_lone ** 2).mean()), r.baseline_mean)

sb = pd.read_csv("results/stacked_brfss.csv")
for y, unit, base in [("menthlth", "days", 3.9), ("fmd", "share", 0.12)]:
    r = sb[(sb.events == "all events") & (sb.outcome == y)].iloc[0]
    add("9 late-night events, stacked by age", {"menthlth": "mentally unhealthy days (of 30)", "fmd": "frequent mental distress"}[y],
        unit, r.est, r.se, r.placebo_sd, base)
ss = pd.read_csv("results/stacked_suicides.csv")
r = ss[ss.events == "all events"].iloc[0]
add("8 late-night events, stacked by age", "suicides (log)", "log", r.est, r.se, r.placebo_sd)
e9 = pd.read_csv("results/988_estimates.csv")
r = e9[(e9.event.str.startswith("2023")) & (e9.outcome == "y_calls") & (~e9.state_trends)].iloc[0]
add("2023 strike, 988 by state popularity", "988 calls (log)", "log", r.est_pct / 100, r.se_pct / 100, r.placebo_sd_pct / 100)

out = pd.DataFrame(rows)
out.to_csv("results/per_viewer_bounds.csv", index=False)

def fmt(v, unit):
    if unit == "days": return f"{v:+.1f} d"
    if unit == "share": return f"{100*v:+.0f} pp"
    return f"{100*(np.exp(v)-1):+.0f}%" if v > -5 else "≤ −99%"
for _, r in out.iterrows():
    cells = [f"[{fmt(r[f'viewer_lo_{s:g}'], r.unit)}, {fmt(r[f'viewer_hi_{s:g}'], r.unit)}]" for s in S]
    print(f"{r.estimate:38s} {r.outcome:32s} pop [{fmt(r.pop_lo, r.unit)}, {fmt(r.pop_hi, r.unit)}]  "
          + "  ".join(f"s={s:.1%}: {c}" for s, c in zip(S, cells)))
