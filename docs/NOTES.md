# Implementation notes — PBT Paper 3 Pipeline

Technical detail of each module, for readers who want to follow or modify the
code. The [README](../README.md) describes what the pipeline does and how to
run it; the manuscript describes the method.

Contents: [data](#0-data-input-data--raw) ·
[InVivo](#a-invivo-real-data--signals) ·
[InSilico](#b-insilico-basal-recommendation-and-meal-scenarios) ·
[metrics](#c-metrics-tables-and-figures) ·
[parameters](#method-parameters) · [units](#units)

---

## 0) data (input data → raw/)

`python 17.ScriptforTestExperiment3.py data` prepares `raw/{id}/` for every participant in `pairs.csv`,
with four files in the T1D‑UOM format: `UoMGlucose{id}.csv` (`bg_ts`, `value`,
mmol/L), `UoMNutrition{id}.csv` (`meal_ts`, `carbs_g`), `UoMBolus{id}.csv`
(`bolus_ts`, `bolus_dose`) and `UoMBasal{id}.csv` (`basal_ts`, `basal_dose`,
`insulin_kind`). Time stamps are `dd/mm/yyyy hh:mm`.

- **`S.GetZenodoData.py`** — T1D‑UOM participants: copies their files from an unzipped `ManchesterCSCoordinatedDiabetesStudy-*` folder in the project root, or downloads the pinned Zenodo record (checked against its MD5) into `data_cache/`
- **`S.ConvertClinicalData.py --to-raw`** — Clinical participants: converts each export (`xt_…_man0NN_ol_sleep.txt`, one per participant, in `Sleep XT files/`) into the four files. Only the sections `Glucose_concentration`, `Enteral_bolus (meal)`, `Insulin_bolus` and `Insulin_infusion` are read; time stamps and values are copied as text. Meal entries with a negative carbohydrate value (corrections in the export) are dropped. `--check` writes to `converted/` and compares with existing files in `raw/`
- **`S.CleanRawData.py`** — Drops blank rows and exact copies; in glucose, keeps the first record when one time stamp carries two values; in boluses, drops a bolus with the same dose as the previous one recorded within 15 minutes (a second record of the same bolus). The originals are kept in `raw/{id}/original/`, with a `cleaning_log.csv`; a file written again by the two scripts above (new input data) replaces the kept original, recognised by the checksum of the last cleaned file

`S.CheckRawData.py` (optional) reports, per file, unreadable time stamps or
values, repeated or unordered time stamps, negative values and values outside
the usual range; it changes nothing.

The Zenodo record of the dataset version is set once, as `ZENODO_RECORD` in
`globals.py`.

---

## A) InVivo (real data → signals)

Builds a 1‑minute composite day without post‑prandial windows, computes the
hourly **relative change** and its **reliability**, and produces the guide
curve, the evaluation days and the virtual‑patient matching.

The orchestrator (`17.RunAllZenodo.py`) checks that `raw/{id}/` holds the four
input files (participants without them are skipped, with a message to run the
data module), cleans `processed/{id}/`, runs the scripts below for each
participant, checks the key outputs, and writes a log per participant and a
summary to `logs/`.

- **1.** `0.GeneratorExamplesZenodo.py` — Splits glucose, meals, bolus and basal by day
- **2–3.** `3.PivotGeneratorZenodo.py`, `3.PivotGeneratorBasalZenodo.py` — 1440‑minute grids for glucose and basal
- **4.** `4.MealBolusDetectionZenodo.py` — Removes 6 h after each of the 4 largest meals (by CHO) per day, on the analysis days
- **5.** `4.MergeBasalZenodo.py` — Merges daily basal files
- **6.** `5.MergeBGCleanZenodo.py` — Merges meal‑free glucose of the analysis days
- **7.** `5.FillGapsBasalZenodo.py` — Representative basal profile (mode per minute)
- **8.** `6.SimulationBasalAutomatedZenodo.py` — Rayleigh insulin‑action curve of the basal profile
- **9–11.** `6.SplitHoursZenodo.py`, `7.InterpolationBGHourlyZenodo.py`, `8.RelativeChangeZenodo.py` — Hourly files, short‑gap interpolation, hourly relative change
- **12–13.** `9.BoxplotZenodo.py`, `10.PivotGeneratormediansZenodo.py` — Hourly medians over every analysis day, and reliability (1 low / 2 medium / 3 high)
- **14–15.** `12.MergeRChBasalNoActZenodo.py`, `13.InterpolationRChZenodo.py` — Guide curve of relative change (`BGRChInt`): hours not of high reliability outside their 25th–75th percentile are set aside and interpolated, then a light smoothing spline
- **16.** `0.InterpolationBGHourlyDataZenodo.py` — Absolute median BG curve (mmol/L) at 1‑minute resolution, the reference for the basal‑only simulation (median across the `BGValue*` day columns only)
- **17.** `S.SaveReservedDays.py` — Saves the files of the two evaluation days to `processed/{id}/Days/`

`12.MergeRChBasalNoActZenodo.py` also saves the figure of the illustrative
participant (`ILLUSTRATIVE_ID` in `globals.py`, 2308) to
`results/invivo/figures/RelativeChange_2308.png` (Figure 1 of the manuscript).

After the orchestrator, `S.BasalMatching.py` computes the daily basal of every
participant and the virtual patient it is matched to.

**Days used.** For each participant, up to 45 days with CGM data are analysed
and the next two days with CGM data are reserved as evaluation days. With fewer
than 47 days of data, the analysis uses all but the last two available days (28
to 45 days across the cohort). The rule is set once, in `globals.day_split`.
When a meal window passes midnight, the rest is removed from the next calendar
day only if that day is an analysis day; after a gap in the record, or on the
last analysis day, the window ends at midnight.

**Daily basal and matching.** The daily basal of a participant is the median of
its daily totals of delivered basal insulin, each obtained by integrating the
basal rate over the day (each reading holds until the next one), or by adding
the doses for long‑acting insulin. The participant is matched to the virtual
patient whose basal rate × 24 is closest. The basal records are used only for
this matching, over the whole available record. The daily bolus (median of the
daily sums of bolus doses, over the days with bolus records) is reported
alongside, as a description of the participant; the recommendation and the
simulated boluses use the correction factor and carbohydrate ratio of the
virtual patient.

**Outputs.** Per participant, in `processed/{id}/`: `SampleJoined{id}.csv`
(guide curve), `BGwNMLeftJoinedHourlyInterpolated{id}.csv` (absolute median BG
curve), and `Days/Day1/`, `Days/Day2/` with the files of the two evaluation
days; their nutrition files hold the four largest meals of the day by
carbohydrate, and `Days/reserved_days.csv` lists the dates. In
`results/invivo/tables/`: `Table1_basal_matching.csv`, with the daily basal and
bolus of every participant, the virtual patient selected and the one in
`pairs.csv` (Table 1 of the manuscript).

---

## B) InSilico (basal recommendation and meal scenarios)

**Simulator step 1 — basal‑only simulation.** In the simulator environment, run
Py‑mgipsim for the virtual patient with its basal profile, open loop and no
meals, and keep the `simulation_settings.json` and `state_results.xlsx` in:

```
simulator_runs/{id}/Simulation_{id2}/
```

`simulator_runs/` holds only what goes into and comes out of the simulator.
`InSilico/simulations/` is a working copy: InSilico rebuilds it from
`simulator_runs/` on every run, and it can be deleted at any time.

**InSilico module.** Run `python 17.ScriptforTestExperiment3.py insilico`. For
each pair in `pairs.csv`, `17.ScriptforTestoPy-mgipsimForEGPTest.py` cleans
`processed/{id}/`, rebuilds `InSilico/simulations/{id}/` with the basal‑only run
from `simulator_runs/`, and runs these steps in order:

- **0.** `0.GeneratorExamplesPy-mgipsimForEGPtest.py` — reads the basal‑only simulation and its starting basal profile
- **3.** `3.PivotGeneratorZenodo.py` — 1440‑minute grid of the day
- **5.** `5.MergeBGCompletePy-mgipsimTest.py`, `5.FillGapsBasalTest.py` — places glucose and basal on the grid
- **6.** `6.SimulationBasalAutomatedTest.py`, `6.SplitHoursTest.py` — insulin action of the basal profile; split by hour
- **7–8.** `7.InterpolationBGHourlyTest.py`, `8.RelativeChangeTest.py` — hourly glucose and relative change
- **9–10.** `9.BoxplotTest.py`, `10.PivotGeneratormediansTest.py` — hourly medians and reliability
- **12–13.** `12.MergeRChBasalNoActTest.py`, `13.InterpolationRChTest.py` — composite day and guide curve
- **14.** `14.SimulationBolusCHOPy-mgipsimTest.py` — flattening: the recommended basal profile
- **15.** `15.GeneratorFileToPy-mgipsimTest.py` — writes the recommended profile into the simulator settings
- **—.** `S.BuildMealScenarios.py` — writes the four meal scenarios (two days, before and after)

- Step 14 sizes a correction for each hour from the deviation of the guide
  curve, assuming it is delivered 2 h before the deviation, and places it there
  in the recommended profile (`LEAD_HOURS = 2`); corrections for the first
  hours of the day therefore fall in the last hours of the (repeating) daily
  profile. A recommended rate cannot be negative: when a reduction is larger
  than the rate, the rate is set to zero and the remaining reduction is
  subtracted 2 h earlier, also bounded at zero.
- Step 15 writes the recommended basal profile into `simulation_settings.json`
  and keeps the starting profile as `simulation_settings_original.json`; step 0
  always reads the starting profile, so every run starts from the same point.
- `S.BuildMealScenarios.py` writes the four scenarios of each participant, with
  the same meals before and after: the four largest meals of each evaluation
  day by carbohydrate, each with a meal‑time bolus from the
  carbohydrate‑to‑insulin ratio of the virtual patient, in open loop.

```
InSilico/simulations/{id}/Simulation_{id2}/       (working copy)
    simulation_settings.json                 recommended basal profile
    simulation_settings_original.json        starting basal profile
    Day1/Before/simulation_settings.json     starting basal + meals of day 1
    Day1/After/simulation_settings.json      recommended basal + meals of day 1
    Day2/Before/ …   Day2/After/ …
    meal_scenarios.csv                       dates, meal times, grams, ratio
```

**Simulator step 2 — scenarios.** Simulate each of the four settings files in
Py‑mgipsim and keep, for each, the settings file simulated and its
`state_results.xlsx` in the matching folder of `simulator_runs/`:

```
simulator_runs/{id}/Simulation_{id2}/Day1/Before/   simulation_settings.json, state_results.xlsx
                                     Day1/After/ …   Day2/Before/ …   Day2/After/ …
```

`InSilico/S.ExportSimulatorRuns.py` creates `simulator_runs/` once from
simulations kept in the earlier layout (inside `InSilico/simulations/`).

---

## C) metrics (tables and figures)

`python 17.ScriptforTestExperiment3.py metrics` empties `results/metrics/` and runs:

- `S.SyncSimulatorResults.py` — copies the result of each scenario from
  `simulator_runs/` into the working copy, only when the settings file it was
  simulated with is identical to the one InSilico has just written; otherwise
  the scenario is reported as to be simulated again, and is not used.
- `S.CollectScenarioResults.py` — reads IG (mmol/L) from every
  `state_results.xlsx` and computes, per participant and day: SD (sample),
  SD reduction, taMAE (mean absolute deviation from 6 mmol/L) and ΔtaMAE, the
  composite stability index *I*, time in range (3.9–10.0 mmol/L), the hourly
  mean bias, the hours within ±15% and the hours with lower variability, and
  the change in daily basal insulin.
- `S.MealCoverage.py` — the share of carbohydrate covered by the four largest
  meals, on the evaluation days and on the analysis days, and the share of the
  glucose readings kept in the composite day that fall within 6 h of a meal not
  excluded or come from days without meal records (Methods and Limitations).
- `S.InputDescriptives.py` — for the data appendix of the thesis chapter: CGM coverage of the analysis days (share
  of the 288 five‑minute slots with a reading, before any exclusion), per
  participant.
- `S.CurveAgreement.py` — agreement between the reconstructed median BG curve
  of each participant and its basal‑only simulation (the manual step). The
  criterion used for every participant is Pearson r ≥ 0.5 over the hours the
  guide keeps (hours with BG data that were not set aside by the interquartile trimming when the
  guide was built; `r_without_grey_and_trimmed_hours`) and a mean absolute
  difference below 1 mmol/L in high‑reliability hours, with the curves centred
  on those hours. It also reports r over the 24 hours, the difference by
  reliability of the hour and the level offset.
- `S.TrimmingEffect.py` — how much the trimming of low‑reliability hours
  changes the guide curve of InVivo (`G.TrimmingEffect.py`, optional, draws it).
  In silico the single basal‑only day makes every hour of high reliability,
  so no hour is trimmed there.
- `S.PowerAnalysisTest.py` — the one‑tailed paired t test of the power
  analysis on the SD before and after, per day, with its 95% CI, observed dz,
  Shapiro–Wilk, Wilcoxon and a Bonferroni check for the two days (with fewer
  than 3 participants, as in the demo, only the SDs are reported). It also
  writes the descriptive statistics of the variables of the test
  (`PowerTestDescriptives.csv`) for the data appendix of the thesis.
- `G.Figures.py` — the figures of the manuscript, sized to be legible at the
  width at which they are printed; both days share the same axis limits.
- `G.CurveCheck.py` — per participant, the reconstructed and simulated curves
  with the hours coloured by reliability and the trimmed hours marked
  (`python G.CurveCheck.py <id>` for one participant, used while building a
  simulator input).
- `G.ScenarioPlot.py` — per participant, simulated glucose before and after
  the recommended basal on the two evaluation days, with the meals and the two
  basal profiles.

`G.TrimmedHoursCheck.py` (optional) confirms that the trimmed hours used by
`S.CurveAgreement.py` are those set aside by `13.InterpolationRChZenodo.py`.

---

## Method parameters

The parameters shared by several steps are set once in `globals.py`:

- **`N_MEALS = 4`** — largest meals per day, excluded in InVivo and simulated in the scenarios
- **`MEAL_WINDOW_HOURS = 6`** — hours of glucose removed after each of those meals
- **`MAX_ANALYSIS_DAYS = 45`**, **`RESERVED_DAYS = 2`** — analysis days and evaluation days of each participant
- **`LEAD_HOURS = 2`** — each basal correction is placed this many hours before the deviation it addresses (step 14)
- **`NEGATIVE_RATE_SHIFT_MIN = 120`** — a reduction larger than the rate is subtracted this many minutes earlier (step 14)
- **`MIN_HIGH_REL_HOURS = 6`** — minimum high‑reliability hours to centre the curves in the agreement check
- **`ILLUSTRATIVE_ID = "2308"`** — participant of the illustrative figures

---

## Units

- **`MGDL_PER_MMOL = 18.0182`** — the single factor used to convert glucose between mmol/L and mg/dL, set in `globals.py`
