# Comedy TV hiatuses and mental health

Do Americans' mental health or loneliness change when popular late-night and comedy TV goes off the air?
Natural experiments: the **2007–08** and **2023** Writers Guild strikes, which took late-night
shows (and, in 2007–08, scripted comedies) off the air for months for reasons unrelated to viewers.

## Data
- **BRFSS 2006–25** (CDC; ~9M interviews): mentally unhealthy days in the past 30 days,
  frequent mental distress (≥14 days), and, from 2023, a direct loneliness item (`SDLONELY`).
- **CDC WONDER** monthly suicide deaths by age group, 1999–2025 (national).
- **Google Trends** pre-strike search interest in each late-night host, by state and nationally.
- **American Time Use Survey** (2003–16, via the CRAN `atus` package): daily TV minutes by age.
- **TVmaze** air dates for every South Park episode and special.
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

## South Park on and off air (`results/southpark_estimates.csv`)
South Park's core audience is young men; historically it ranked #1 among men 18–34. Its schedule varies a lot from year to year,
e.g. there was no regular season from April 2023 to July 2025 (only three Paramount+ specials), and the Season 27 premiere was pushed back two weeks in July 2025.
Exposure = new South Park releases (TVmaze air dates: 353 episodes and specials, including Paramount+ specials) per month,
or in the respondent's 30-day recall window. Calendar-month or week-of-year fixed effects remove the show's usual spring/fall
rhythm. Triple differences compare young men with everyone else in the same month (suicides) or on the same interview day
(BRFSS). Placebos shift the whole episode calendar by ±1–12 years (suicides) or ±1–3 years (BRFSS).
If going off air hurt fans, the estimates per new episode would be *negative*.

| Outcome | Comparison | Per new episode | Placebo SD | p |
|---|---|---|---|---|
| Suicides, men 15–34 | own history (year + calendar-month FE) | +0.11% | 0.18% | 0.62 (placebo) |
| Suicides, men 15–34 | vs all other sex-age groups, same month | +0.05% | 0.23% | 0.92 (placebo) |
| Suicides, men 15–34 | vs others, Apr 2023–Jun 2025 gap as a whole | +0.09% total | | 0.96 |
| Mentally unhealthy days, men 18–34 | vs others, same day | +0.008 days | 0.020 | 0.77 |
| Frequent distress, men 18–34 | vs others, same day | +0.05 pp | 0.08 pp | 0.51 |
| Lonely, men 18–34 (2023–25) | vs others, same day | +0.84 pp | 1.5 pp | 0.06 (clustered SE) |

No sign that young men did worse when South Park was off the air. That includes the two-year gap, during which young men's
suicides tracked other groups almost exactly (+0.1% ± 1.8%). Every per-episode estimate has the wrong sign for a "missing the show"
effect and inside the placebo range.

## Stacked DiD: shows that paused, ended or were replaced, by age-group viewing (`results/stacked_*.csv`, `fig4_stacked_events.png`)
Nine late-night events (`data/show_events.csv`):
- **Paused:** the 2007–08 strike, the 2023 strike, Kimmel's 2025 suspension.
- **Ended:** Conan leaving The Tonight Show in 2010, the Colbert Report ending in 2014, Letterman retiring in 2015.
- **Replaced:** Leno → Conan in 2009, Leno's final Tonight Show in 2014, Jon Stewart leaving in 2015.

Each show's audience age profile is calibrated to its reported Nielsen median viewer age:
ATUS TV time by single year of age is tilted until its median matches (`src/show_profiles.py`, `results/show_age_profiles.csv`).
Sources for the medians are listed in the events file. Leno and Letterman ≈55–60 put their audiences 2–3× the population rate among people 75+;
Conan, Colbert Report and Stewart (33–41) over-index on people under 35.

Model, stacked across events: y = β · (share of period the show was gone) × (age group's viewing rate − 1)
+ event×age-group FE + event×period FE. β compares age groups that watched more vs less *in the same event and
period*. Suicides use national month × ten-year age, ±12 months. BRFSS uses interview day × five-year age, ±6 months, with state FE;
2010–21 BRFSS files were added for this. Placebos move every event by ±1–3 years.

| Outcome | Events | Per +1 viewing rate | SE | p | Placebo SD |
|---|---|---|---|---|---|
| Suicides | all 8 with data | +1.2% | 0.9 | 0.19 | 1.5% |
| Suicides | paused (2) | +2.2% | 1.9 | 0.27 | 5.8% |
| Suicides | ended/replaced (6) | +1.0% | 1.0 | 0.31 | 1.5% |
| Mentally unhealthy days | all 9 | −0.03 | 0.04 | 0.46 | 0.06 |
| Mentally unhealthy days | paused (3) | +0.03 | 0.13 | 0.80 | 0.24 |
| Mentally unhealthy days | ended/replaced (6) | −0.04 | 0.05 | 0.42 | 0.07 |
| Frequent distress | all 9 | −0.1 pp | 0.1 | 0.68 | 0.3 pp |

- Nothing exceeds its placebo spread, and the survey estimates are essentially zero.
- One pattern is worth a follow-up: 7 of the 8 per-event suicide estimates are positive, i.e. the shows' heavier-viewing age groups
  were slightly up while the show was gone. The pooled +1.2% is still within the placebo SD, and differing age trends in suicide
  within the 24-month windows could produce it. Adding age-specific trends, or state-level data, would test it.
- The 2007–08 strike is the only single event with a significant survey estimate (+0.47 days, p≈0.03). It is not robust:
  Conan's exit gives −0.37 in the other direction, and with 9 events one nominal hit is expected by chance.

Caveats: the median ages come from scattered trade-press reports (2009–2015), and several are proxies
(Conan's TBS-era median, 2015 medians used for 2023 and 2025). No public age data exist for sitcom finales such as
The Office or Big Bang Theory, so they are not included. The tilted-ATUS profile is a model of each audience, not measured viewing.

## Comedy replaced by other programming (`results/replaced_*.csv`)
**NBC Olympics.** The Tonight Show is preempted by Games coverage for ~2.5 weeks every two years
(`data/replacement_events.csv`; NBC confirmed Paris 2024 as Jul 29–Aug 12; in 2018 a 5-minute "Fallon 5" aired instead).
2010 and 2014 are dropped because they overlap the Conan exit and Leno's finale. The stacked DiD is the same as above, using a
Tonight Show age profile (Leno 55, Fallon 54.3).

| Outcome | Events | Per +1 viewing rate | SE | p | Placebo SD | Placebo p |
|---|---|---|---|---|---|---|
| Suicides | 10 Games, 2002–24 | −0.2% | 3.1 | 0.94 | 2.5% | 1.00 |
| Suicides | excluding Tokyo 2021 | −1.0% | 3.2 | 0.75 | 2.7% | 0.83 |
| Mentally unhealthy days | 7 Games with BRFSS, 2008–24 | +0.08 | 0.14 | 0.58 | 0.18 | 0.83 |
| Mentally unhealthy days | excluding Tokyo 2021 | +0.27 | 0.12 | 0.04 | 0.19 | 0.17 |
| Frequent distress | 7 Games | +0.2 pp | 0.6 | 0.75 | 0.8 pp | 0.67 |

The survey estimate is fragile. With the four Games first available it was +0.30 (p=0.04). Adding 2018, 2021 and 2022
(BRFSS 2017–21 were downloaded for this) brings it to +0.08. Dropping COVID-era Tokyo brings it back to +0.27, but that is
within 1.4 placebo SDs (placebo p=0.17). Per-Games estimates range from −1.2 (2021) to +1.3 (2024). The Olympics also skew
old, so this is the net effect of swapping comedy for sports, not of losing TV.

**CBS 12:37am.** After Midnight's last episode aired June 12, 2025; reports conflict on whether *Comics Unleashed* filled the slot.
There is no audience age data, so this uses the population-level strike design (2025 vs the same weeks of 2023–24).
The estimates are −0.20 days (p<0.001) and −0.9 pp frequent distress, i.e. *better* after the show ended, while fake endings
in 2023/2024 give +0.13 and +0.07. With an audience of well under 1% of adults, a population shift this size cannot come from the show.
It reflects something else in mid/late 2025 (e.g. the 2025 BRFSS fieldwork) and shows the limit of designs without an exposed group.

## Reproduce
```
pip install pandas pyreadstat pyarrow pyfixest matplotlib requests pytrends pyreadr
./src/download_brfss.sh            # ~1.8 GB zipped, ~19 GB unzipped, into data/raw/
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
python3 src/wonder.py D76 data/wonder/d76_month_sex_age.csv V7 V5
python3 src/wonder.py D176 data/wonder/d176_month_sex_age.csv V7 V5
python3 src/southpark_episodes.py
PYTHONPATH=src python3 src/analysis_southpark.py
python3 src/show_profiles.py
PYTHONPATH=src python3 src/analysis_stacked.py            # suicides
PYTHONPATH=src python3 src/analysis_stacked.py --brfss    # BRFSS
python3 src/show_profiles.py data/replacement_events.csv results/replacement_age_profiles.csv
PYTHONPATH=src python3 src/analysis_replaced.py           # suicides
PYTHONPATH=src python3 src/analysis_replaced.py --brfss   # BRFSS
python3 src/plots.py
```
