"""Extract the BRFSS variables we need from each annual file into one parquet file."""
import glob, os
import numpy as np, pandas as pd, pyreadstat

COLS = ["IDATE", "_STATE", "MENTHLTH", "POORHLTH", "GENHLTH", "_AGEG5YR", "MARITAL",
        "NUMADULT", "HHADULT", "_LLCPWT", "_FINALWT", "SDLONELY", "LSATISFY", "EMTSUPRT",
        "SEX", "SEXVAR", "_EDUCAG"]

def days(x):
    """BRFSS 'days in past 30' coding: 1-30 days, 88 = none, 77/99 = don't know/refused."""
    x = x.where(~x.isin([77, 99]))
    return x.where(x != 88, 0).where(lambda v: v <= 30)

frames = []
for f in sorted(glob.glob("data/raw/*.XPT")):
    _, meta = pyreadstat.read_xport(f, metadataonly=True, encoding="latin1")
    use = [c for c in COLS if c in meta.column_names]
    df, _ = pyreadstat.read_xport(f, usecols=use, encoding="latin1")
    out = pd.DataFrame({
        "file": os.path.basename(f),
        "date": pd.to_datetime(df["IDATE"].astype(str).str.strip(), format="%m%d%Y", errors="coerce"),
        "state": df["_STATE"].astype("Int64"),
        "menthlth": days(df["MENTHLTH"]),
        "genhlth_poor": df["GENHLTH"].map({1: 0, 2: 0, 3: 0, 4: 1, 5: 1}),
        "agegrp": df["_AGEG5YR"].where(df["_AGEG5YR"] < 14),  # 1=18-24 ... 13=80+
        "married": df["MARITAL"].map({1: 1, 2: 0, 3: 0, 4: 0, 5: 0, 6: 1}),
        "sex_female": (df["SEXVAR"] if "SEXVAR" in df else df["SEX"]).map({1: 0, 2: 1}),
        "educ": df["_EDUCAG"].where(df["_EDUCAG"] < 9),
        "weight": df["_LLCPWT"] if "_LLCPWT" in df else df["_FINALWT"],
    })
    adults = df["NUMADULT"] if "NUMADULT" in df else pd.Series(np.nan, index=df.index)
    if "HHADULT" in df:
        adults = adults.fillna(df["HHADULT"])
    out["lives_alone"] = np.where(adults.isna() | (adults > 76), np.nan, (adults == 1).astype(float))
    # SDLONELY: how often lonely, 1=always ... 5=never; 7/9 missing.
    if "SDLONELY" in df:
        out["lonely"] = df["SDLONELY"].map({1: 1, 2: 1, 3: 1, 4: 0, 5: 0})  # always/usually/sometimes
    frames.append(out)
    print(f, len(out))

d = pd.concat(frames, ignore_index=True)
d = d[d.date.notna()]
d["fmd"] = (d.menthlth >= 14).astype(float).where(d.menthlth.notna())  # frequent mental distress
d.to_parquet("data/interim/brfss.parquet")
print(d.groupby(d.date.dt.year).agg(n=("menthlth", "size"), menthlth=("menthlth", "mean"), lonely=("lonely", "mean")))
