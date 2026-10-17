# Comedy TV hiatuses and mental health

Do Americans' mental health or loneliness change when popular late-night and comedy TV goes off the air?
Natural experiments: the **2007–08** and **2023** Writers Guild strikes, which took late-night
shows (and, in 2007–08, scripted comedies) off the air for months for reasons unrelated to viewers.

## Data
- **BRFSS 2006–09, 2022–25** (CDC; ~3.4M interviews): mentally unhealthy days in the past 30 days,
  frequent mental distress (≥14 days), and, from 2023, a direct loneliness item (`SDLONELY`).
- **CDC WONDER** monthly suicide deaths by age group, 1999–2025 (national).
- **Google Trends** pre-strike search interest in each late-night host, by state and nationally.
- **American Time Use Survey** (2003–16, via the CRAN `atus` package): daily TV minutes by age.
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

## Suicide deaths (`results/suicide_estimates.csv`, `fig3_suicides.png`)
National monthly suicide deaths by age group, 1999–2025, from CDC WONDER: final data through 2017,
then the provisional database. The API only gives national totals. Model: log suicides per day =
hiatus share of the month + year + calendar-month fixed effects. For inference, a hiatus of the same length is placed at
every possible start month in non-event years (~250 placebos), and the real estimate is ranked against them.

| Event | Group | Change in suicides | Typical placebo swing (SD) | Placebo p |
|---|---|---|---|---|
| 2023 strike | All ages | +0.1% | 2.4% | 0.95 |
| 2023 strike | 55+ | +1.5% | 2.8% | 0.54 |
| 2023 strike | 55+ relative to under-55 | +2.3% | 2.5% | 0.27 |
| 2007–08 strike (scripted + late night) | All ages | +1.5% | 2.5% | 0.46 |
| 2007–08 strike (late night only) | 55+ | +4.1% | 3.6% | 0.25 |

None of the estimates stands out from ordinary month-to-month noise. Normal fluctuation is about ±2.5%, so an effect
smaller than about 5% (roughly 200 deaths a month nationally) could not be detected. Kimmel's 6-day
suspension is far too short for monthly data (placebo SD 19%). 2025 counts are provisional.

## Weighted by pre-strike show popularity (`results/popularity_weighted_*.csv`)
Exposure becomes a dose. For each show that went dark, take its Google Trends search interest in the
respondent's state over the 12 months before the strike (`data/trends/`). Weight it by the show's national
pre-strike interest, multiply by the share of the 30-day recall window the show was dark (using each show's
own dates, e.g. Kimmel came back Oct 24, 2023), and sum over shows. 1 = an average-popularity state with every
show dark all month. State popularity ranges 0.59–1.72 in 2023 and 0.76–1.28 in 2007.

| | Mentally unhealthy days | Frequent distress | Lonely |
|---|---|---|---|
| 2023, weighted dose | +0.11 (p=0.30) | +0.5 pp (p=0.29) | **+1.4 pp (p=0.03)** |
| 2023, extra effect per +1 state popularity | +0.29 (p=0.16) | +1.1 pp (p=0.28) | +0.9 pp (p=0.60) |
| 2007–08, weighted dose | −0.07 (p=0.44) | −0.4 pp (p=0.33) | n/a |
| 2007–08, extra effect per +1 state popularity | −0.49 (p=0.34) | −1.4 pp (p=0.49) | n/a |

- **Loneliness is the one suggestive result.** The weighted effect is +1.4 pp. It holds against each
  comparison year separately (+1.3 pp, p≈0.07) and against 2025 using May–December only (+1.3 pp).
  Fake strikes in 2024 and 2025 produce only ±0.3 pp.
- **But there is no dose-response.** States that searched for these shows more did not become lonelier during the strike.
  If losing the shows caused loneliness, they should have. So the loneliness bump looks like a nationwide feature of
  mid-2023 rather than an effect of the shows. Fake-strike checks on the cross-state comparison give values from −0.45 to +0.01 days (mentally unhealthy days) and −0.01 to +0.01 (loneliness), so the real estimates sit inside the noise.
- **Suicides, both strikes pooled** (each weighted by the national pre-strike popularity of the shows that went dark):
  +1.4% at peak dose for all ages (placebo SD 2.8%, p=0.60), +3.6% for 55+ (p=0.32), and +0.2% for under 55 (p=0.91).
- **Limits of the popularity measure.** Google Trends measures *search* interest, not viewing. It over-represents
  younger, online audiences (e.g. the Daily Show outranks Leno in 2007 despite a much smaller TV audience),
  and comparisons across eras reflect how internet use changed. Local Nielsen ratings by market would be better if you can get them.

## Also weighted by age group's TV propensity (`results/age_weighted_*.csv`)
How likely each age group is to watch comes from the American Time Use Survey: weighted mean daily TV minutes by
age, relative to the population mean (`results/atus_tv_by_age.csv`). The 2003–06 diaries are used for the
2007 strike and the 2013–16 diaries, the latest in the open copy, for 2023. Viewing rises steeply with age: 15–34-year-olds
watch about 0.8× the average and 75+ about 1.6× (≈130 vs ≈260 min/day). Each respondent's dose = age propensity ×
state show-popularity dose from the section above.

| | Poor mental-health days | Frequent distress | Lonely |
|---|---|---|---|
| 2023, age × popularity weighted | +0.08 (p=0.46) | +0.4 pp (p=0.35) | +1.0 pp (p=0.13) |
| 2023, extra per +1 age propensity | +0.03 (p=0.89) | +0.3 pp (p=0.67) | +0.9 pp (p=0.62) |
| 2007–08, age × popularity weighted | −0.03 (p=0.74) | −0.2 pp (p=0.53) | n/a |
| 2007–08, extra per +1 age propensity | +0.49 (p=0.13) | +2.0 pp (p=0.13) | n/a |

The "extra" rows use age-specific season and week fixed effects, so they test only whether heavier-viewing ages
changed more than lighter-viewing ages *at the same time*. Fake strikes give −0.02 to +0.36 days and −2.5 to +0.3 pp of
loneliness on the same test. The only hint is 2007–08: older, heavier-viewing ages rose relative to younger ones
(+0.49 days per unit of propensity), but this is not significant and is within the placebo range.

Suicides, as a month × ten-year age group panel (ages 15+) with dose = age propensity × national popularity-weighted
dark share:
- with age×year and age×calendar-month FE: +2.2% per unit dose (placebo SD 2.8%, p=0.36);
- adding month FE, so the estimate comes only from differences between ages within the same month: +5.5% (placebo SD 7.6%, p=0.47).

Limits: the open ATUS copy (CRAN `atus`, 2003–16) has no clock times, so this is *total* TV time by age, not
late-night viewing, and the 2023 profile is several years old. The full BLS files (2003–2024, with activity start times)
would allow propensity to watch during the 11:35pm–12:35am slot specifically, from 2019–22 diaries. BLS blocks
automated downloads that don't identify a contact.

## Reproduce
```
pip install pandas pyreadstat pyarrow pyfixest matplotlib requests pytrends pyreadr
./src/download_brfss.sh            # ~650 MB zipped, ~7 GB unzipped, into data/raw/
python3 src/extract_brfss.py
python3 src/pageviews.py
python3 src/wonder.py D76 data/wonder/d76_month_age.csv V5     # 1999-2020 (used through 2017)
python3 src/wonder.py D176 data/wonder/d176_month_age.csv V5    # 2018-present provisional
PYTHONPATH=src python3 src/analysis_strikes.py
PYTHONPATH=src python3 src/analysis_suicide.py
python3 src/trends.py                                           # Google Trends, cached in data/trends/
PYTHONPATH=src python3 src/analysis_popularity.py
# ATUS (abridged, 2003-16): curl -O https://cran.r-project.org/src/contrib/Archive/atus/atus_0.2.tar.gz into data/raw/atus_pkg and untar
python3 src/atus_age.py
PYTHONPATH=src python3 src/analysis_age.py
python3 src/plots.py
```
