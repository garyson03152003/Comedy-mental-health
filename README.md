# Comedy TV hiatuses and mental health

Do Americans' mental health or loneliness change when popular late-night and comedy TV goes off the air?
Natural experiments: the **2007–08** and **2023** Writers Guild strikes, which took late-night
shows (and, in 2007–08, scripted comedies) off the air for months for reasons unrelated to viewers.

## Data
- **BRFSS 2006–09, 2022–25** (CDC; ~3.4M interviews): mentally unhealthy days in the past 30 days,
  frequent mental distress (≥14 days), and, from 2023, a direct loneliness item (`SDLONELY`).
- **Wikipedia pageviews** for five nightly late-night shows, a stand-in for audience attention.

## Design
For each interview date, `exp` = share of the respondent's 30-day recall window inside the hiatus.
Strike-year interviews are compared with the same calendar weeks in neighbouring years
(season, week-of-season and state×season fixed effects; age, sex, education controls;
survey weights; SEs clustered by state). A triple difference tests whether adults aged 50+
living alone (heavy, companionship-style viewers) were hit harder. Placebos assign a fake strike to non-strike years.

## Results (`results/strike_estimates.csv`)
**The strike really reduced attention.** Views of late-night shows' Wikipedia pages fell by roughly
35–40% relative to 2022/2024 while the shows were off air, and recovered when they returned (`fig1_pageviews.png`).

**No detectable effect on mental health.** Effects are for a full 30-day recall window spent in the hiatus.

| Event | Outcome | Effect | 95% CI | Baseline |
|---|---|---|---|---|
| 2023 strike | Mentally unhealthy days | +0.08 days | −0.10 to +0.27 | 4.9 |
| 2023 strike | Frequent mental distress | +0.4 pp | −0.4 to +1.1 | 15.7% |
| 2023 strike | Lonely (at least sometimes) | +1.1 pp | −0.1 to +2.4 | 32% |
| 2023 strike | Extra effect, 50+ living alone (days) | −0.15 days | −0.57 to +0.27 | |
| 2007–08 strike | Mentally unhealthy days | −0.12 days | −0.26 to +0.02 | 3.4 |
| 2007–08 strike | Extra effect, 50+ living alone (days) | +0.16 days | −0.06 to +0.39 | |

Caveats that matter:
- **Normal year-to-year swings are bigger than the strike estimates.** Fake "strikes" in 2022 or 2024 produce
  ±0.25 days (nominally p<0.01), so state-clustered SEs understate the true uncertainty for mentally unhealthy days.
  The fake strikes for loneliness are small (±0.4 pp), so the +1.1 pp loneliness estimate stands out more,
  but it is not significant and shrinks to +0.6 pp against 2025 alone.
- The event study (`fig2_event_study_2023.png`) shows 2023 was higher on mentally unhealthy days *before* the strike
  as well, and the loneliness gap comes mostly from a low January–March. Neither shows a jump at the strike.
- The 2008/09 comparison season overlaps the financial crisis, which may bias the 2007–08 estimate downward.
- BRFSS has no TV-viewing data; "50+ living alone" is only a proxy for heavy viewers who watch for companionship.
- Too short for the 30-day measure: Kimmel's 6-day suspension (Sept 2025). Data not yet released: the Colbert finale (May 2026).

**Bottom line:** the population-level effect of a months-long comedy hiatus is small, under about a quarter of a day
per month, or under 2 points of loneliness. This contrasts with the fan surveys (e.g. Lather & Moyer-Gusé 2011),
which find distress among strongly attached viewers. Those viewers are probably too few to move population averages.
Testing them directly needs viewing data (e.g. ATUS, or a panel survey with TV items).

## Reproduce
```
pip install pandas pyreadstat pyarrow pyfixest matplotlib requests
./src/download_brfss.sh            # ~650 MB zipped, ~7 GB unzipped, into data/raw/
python3 src/extract_brfss.py
python3 src/pageviews.py
PYTHONPATH=src python3 src/analysis_strikes.py
python3 src/plots.py
```
