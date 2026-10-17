"""Hiatus events for popular US comedy/late-night TV."""
import pandas as pd

# start = last original episode / day shows went dark; end = first new episodes back.
EVENTS = {
    # 2007-08 WGA strike: late night went to reruns Nov 5 2007, returned (mostly without writers) Jan 2 2008.
    "wga2007_latenight": ("2007-11-05", "2008-01-02"),
    # Scripted primetime comedies were largely dark until the strike ended Feb 12 2008 (+ ~6 weeks to new episodes).
    "wga2007_scripted": ("2007-11-05", "2008-03-31"),
    # 2023 WGA strike: late night dark May 2 2023; returned Oct 2 2023 (SNL Oct 14).
    "wga2023_latenight": ("2023-05-02", "2023-10-02"),
    # Jimmy Kimmel Live! suspended by ABC Sept 17 2025, returned Sept 23 2025.
    "kimmel2025": ("2025-09-18", "2025-09-23"),
}

def window(name):
    s, e = EVENTS[name]
    return pd.Timestamp(s), pd.Timestamp(e)
