"""988 Suicide & Crisis Lifeline contacts by state and month (GAO-26-108114 data, Jul 2022 - Sep 2025).

Cross-state dose-response: did states that liked a show more see larger changes in 988 contacts in
the months the show was off air (or on air)?

    log(routed calls)_st = beta * D_t * (P_s - mean P) + state FE + month FE [+ state trends]

D_t = share of month t the show was gone (strike, Olympics, Kimmel) or the number of new South Park
releases in month t. P_s = pre-event Google Trends popularity in state s (average state = 1).
Month FE absorb national swings (988's launch ramp, seasonality, news); a state x post-Sep-2024 FE
absorbs the switch from area-code routing to georouting.
Placebo: same-length windows placed at every other start month (or the South Park calendar
shifted by +-1..12 months), same state popularity.
"""
import numpy as np, pandas as pd, pyfixest as pf
from analysis_popularity import weights, FIPS
from analysis_southpark import ep as sp_dates

ABBR = dict(AL="Alabama", AK="Alaska", AZ="Arizona", AR="Arkansas", CA="California", CO="Colorado", CT="Connecticut",
    DE="Delaware", DC="District of Columbia", FL="Florida", GA="Georgia", HI="Hawaii", ID="Idaho", IL="Illinois",
    IN="Indiana", IA="Iowa", KS="Kansas", KY="Kentucky", LA="Louisiana", ME="Maine", MD="Maryland", MA="Massachusetts",
    MI="Michigan", MN="Minnesota", MS="Mississippi", MO="Missouri", MT="Montana", NE="Nebraska", NV="Nevada",
    NH="New Hampshire", NJ="New Jersey", NM="New Mexico", NY="New York", NC="North Carolina", ND="North Dakota",
    OH="Ohio", OK="Oklahoma", OR="Oregon", PA="Pennsylvania", RI="Rhode Island", SC="South Carolina", SD="South Dakota",
    TN="Tennessee", TX="Texas", UT="Utah", VT="Vermont", VA="Virginia", WA="Washington", WV="West Virginia",
    WI="Wisconsin", WY="Wyoming")

d = pd.read_csv("data/988/GAO-26-108114_State-by-State_988_Lifeline_Performance.csv")
d = d[d.State.isin(ABBR)].copy()
d["month"] = pd.to_datetime(d.Timeframe, format="%B %Y")
d = d[d.month >= "2022-08-01"]            # 988 launched Jul 16 2022: drop the partial month
d["fips"] = d.State.map(ABBR).map(FIPS)
d["contacts"] = d[["Number of Routed Calls", "Number of Routed Texts", "Number of Routed Chats"]].fillna(0).sum(axis=1)
d["y_calls"] = np.log(d["Number of Routed Calls"])
d["y_all"] = np.log(d.contacts)
d["t"] = (d.month.dt.year - 2022) * 12 + d.month.dt.month
d["state_post"] = d.State + (d.month >= "2024-09-01").astype(str)

def pop_single(key):
    s = pd.read_csv(f"data/trends/{key}_states.csv", index_col=0).iloc[:, 0]
    s.index = s.index.map(FIPS)
    return s / s.mean()

def pop_2023():
    w, st = weights("wga2023")
    shows = ["Jimmy Fallon", "Stephen Colbert", "Jimmy Kimmel"]
    return (st[shows] * (w[shows] / w[shows].sum())).sum(axis=1)

def month_share(start, end):
    m0 = d.month.values.astype("datetime64[D]")
    m1 = (d.month + pd.offsets.MonthBegin(1)).values.astype("datetime64[D]")
    lo, hi = np.maximum(m0, np.datetime64(start, "D")), np.minimum(m1, np.datetime64(end, "D"))
    return np.clip((hi - lo).astype(int), 0, None) / (m1 - m0).astype(int)

def fit(D, P, y="y_calls", trends=False):
    x = d.assign(DP=D * (d.fips.map(P) - d.fips.map(P).mean()))
    rhs = "DP" + (" + C(State):t" if trends else "")
    m = pf.feols(f"{y} ~ {rhs} | State + month + state_post", data=x.dropna(subset=["DP", y]), vcov={"CRV1": "State"})
    return m.tidy().loc["DP"]

EVENTS = {
    "2023 writers' strike (late night)": ("window", "2023-05-02", "2023-10-02", pop_2023),
    "2024 Olympics (Tonight Show preempted)": ("window", "2024-07-29", "2024-08-12", lambda: pop_single("olympics2024_fallon")),
    "Kimmel suspension (Sep 2025)": ("window", "2025-09-18", "2025-09-23", lambda: pop_single("kimmel2025")),
    "South Park new episodes (per release)": ("episodes", None, None, lambda: pop_single("southpark_gap2023")),
}

if __name__ == "__main__":
    rows = []
    months = pd.date_range("2022-08-01", "2025-09-01", freq="MS")
    for label, (kind, s, e, popf) in EVENTS.items():
        P = popf()
        if kind == "window":
            D = month_share(s, e)
            L = pd.Timestamp(e) - pd.Timestamp(s)
            fakes = [month_share(m + (pd.Timestamp(s) - pd.Timestamp(s).normalize().replace(day=1)), m + (pd.Timestamp(s) - pd.Timestamp(s).replace(day=1)) + L)
                     for m in months if abs((m - pd.Timestamp(s).replace(day=1)).days) > 62 and m + L <= months[-1] + pd.offsets.MonthEnd(0)]
        else:
            c = sp_dates.dt.to_period("M").value_counts()
            D = d.month.dt.to_period("M").map(c).fillna(0).values
            fakes = [d.month.dt.to_period("M").map((sp_dates + pd.DateOffset(months=k)).dt.to_period("M").value_counts()).fillna(0).values
                     for k in range(-12, 13) if k]
        for y in ["y_calls", "y_all"]:
            for trends in (False, True):
                t = fit(D, P, y, trends)
                pl = np.array([fit(F, P, y, trends).Estimate for F in fakes])
                rows.append(dict(event=label, outcome=y, state_trends=trends, est_pct=100 * t.Estimate, se_pct=100 * t["Std. Error"],
                                 p=t["Pr(>|t|)"], placebo_sd_pct=100 * pl.std(), placebo_p=(np.abs(pl) >= abs(t.Estimate)).mean(),
                                 n_placebos=len(pl)))
                print(f"{label:40s} {y:7s} trends={str(trends):5s} {100*t.Estimate:+7.2f}% per +1 popularity "
                      f"(se {100*t['Std. Error']:.2f}, p={t['Pr(>|t|)']:.2f}); placebo SD {100*pl.std():.2f}%, "
                      f"placebo p={(np.abs(pl) >= abs(t.Estimate)).mean():.2f} (n={len(pl)})")
    pd.DataFrame(rows).to_csv("results/988_estimates.csv", index=False)
