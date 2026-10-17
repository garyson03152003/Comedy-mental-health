"""Figures for the strike analysis."""
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
BLUE, GRAY, SHADE = "#2a78d6", "#8a8984", "#f0efec"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False})

# 1. Attention: weekly Wikipedia views of the 5 nightly late-night shows, 2023 vs 2022/2024
pv = pd.read_csv("results/pageviews_daily.csv", parse_dates=["date"])
nightly = ["The_Tonight_Show_Starring_Jimmy_Fallon", "The_Late_Show_with_Stephen_Colbert",
           "Jimmy_Kimmel_Live!", "Late_Night_with_Seth_Meyers", "The_Daily_Show"]
pv = pv[pv.show.isin(nightly)]
pv["year"], pv["week"] = pv.date.dt.year, pv.date.dt.isocalendar().week.clip(upper=52)
w = pv[pv.year.isin([2022, 2023, 2024])].groupby(["year", "week"]).views.sum().unstack(0)
w = w / w.loc[1:17].mean()  # index: Jan-Apr average of each year = 1
fig, ax = plt.subplots(figsize=(7, 3.4))
ax.axvspan(18, 40, color=SHADE, zorder=0)
ax.text(29, 0.36, "2023 strike: late night off air", ha="center", color=INK2, fontsize=9)
ax.plot(w.index, (w[2022] + w[2024]) / 2, color=GRAY, lw=2, label="2022 & 2024 average")
ax.plot(w.index, w[2023], color=BLUE, lw=2, label="2023")
ax.axhline(1, color=GRID, lw=1, zorder=0)
ax.set_xlabel("Week of year"); ax.set_ylabel("Wikipedia views (Jan–Apr = 1)"); ax.set_ylim(0.3, 1.9)
ax.set_title("Attention to late-night shows fell during the 2023 strike", loc="left", color=INK, fontsize=11)
ax.legend(frameon=False, loc="upper right")
fig.tight_layout(); fig.savefig("results/fig1_pageviews.png", dpi=160)

# 2. Event study: 2023 minus 2022/2024 (2024/2025 for loneliness), by interview month, April = 0
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
for ax, (f, title, scale, unit) in zip(axes, [
        ("menthlth", "Mentally unhealthy days (past 30)", 1, "days"),
        ("lonely", "Lonely at least sometimes", 100, "percentage points")]):
    t = pd.read_csv(f"results/event_study_2023_{f}.csv", index_col=0)
    t["month"] = t.index.str.extract(r"month::(\d+)")[0].astype(int).values
    t = pd.concat([t, pd.DataFrame({"Estimate": [0], "Std. Error": [0], "month": [4]})]).sort_values("month")
    ax.axvspan(5, 10.5, color=SHADE, zorder=0)
    ax.axhline(0, color=GRID, lw=1)
    ax.errorbar(t.month, t.Estimate * scale, yerr=1.96 * t["Std. Error"] * scale, fmt="o",
                color=BLUE, ms=6, lw=2, capsize=0)
    ax.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    ax.set_title(title, loc="left", color=INK, fontsize=10)
    ax.set_ylabel(f"2023 vs comparison years ({unit})")
axes[0].text(7.75, axes[0].get_ylim()[1] * 0.92, "strike*", ha="center", color=INK2, fontsize=9)
fig.text(0.01, 0.01, "*Shaded: months whose 30-day recall overlaps the strike. Bars: 95% CI, state-clustered. "
         "Reference month: April 2023.", fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig("results/fig2_event_study_2023.png", dpi=160)

# 3. Suicides: monthly deviation from year + calendar-month pattern, around each strike
import numpy as np, pyfixest as pf, matplotlib.dates
sm = pd.read_csv("results/suicides_monthly.csv", parse_dates=["month"])
sm["resid"] = pf.feols("y ~ 1 | year + moy", data=sm).resid()
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
for ax, (lo, hi, s, e, title) in zip(axes, [
        ("2006-01-01", "2009-12-31", "2007-11-05", "2008-03-31", "2007–08 strike"),
        ("2022-01-01", "2024-12-31", "2023-05-02", "2023-10-02", "2023 strike")]):
    x = sm[(sm.month >= lo) & (sm.month <= hi)]
    ax.axvspan(pd.Timestamp(s), pd.Timestamp(e), color=SHADE, zorder=0)
    ax.axhline(0, color=GRID, lw=1)
    ax.plot(x.month, 100 * x.resid, color=BLUE, lw=2, marker="o", ms=4)
    ax.set_title(title, loc="left", color=INK, fontsize=10)
    ax.xaxis.set_major_locator(matplotlib.dates.YearLocator())
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
axes[0].set_ylabel("Suicides vs expected (%)")
fig.text(0.01, 0.01, "Deviation of log daily suicides from year and calendar-month averages, US 1999–2025 "
         "(CDC WONDER). Shaded: hiatus.", fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig("results/fig3_suicides.png", dpi=160)
