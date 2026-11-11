# Personalised Basal Tuner (PBT) — Paper 3 Pipeline (Recommender, In‑Silico)

PBT generates **basal rate recommendations** from real CGM and pump data and
evaluates them **in silico** with Py‑mgipsim (two simulated days with meals).
The repository is organised in four modules, run in this order:
**data → InVivo → InSilico → metrics**.

This pipeline accompanies the manuscript *Towards a Personalised Basal Tuner:
Recommending Optimised Basal Insulin Rates for Improved Glycaemic Control in
Type 1 Diabetes*. See [docs/Paper3_Context.md](./docs/Paper3_Context.md) for
the scientific background.

---

## Folder structure

```
17.ScriptforTestExperiment3.py   launcher: choose the module to run
globals.py      the single configuration file, used by every module
pairs.csv       real participant -> virtual patient, and the source of each participant
data/           input data: download, conversion of the clinical exports, cleaning, checks
raw/            input data of every participant (raw/{id}/), written by data/
simulator_runs/ what goes into and comes out of Py-mgipsim, kept by the user
py-mgipsim/     the simulator (cloned separately, see Environments)
InVivo/         real data: composite day, guide curve, evaluation days, matching
InSilico/       basal recommendation and meal scenarios on the virtual patient
metrics/        metrics, tables and figures of the before/after scenarios
results/        final tables and figures, one subfolder per module
sample_data/    demo input: participant 2308 and its Py-mgipsim runs
compare_results.py   compares every table of two runs
LICENSE  •  CITATION.cff  •  requirements.txt
```

There is one `globals.py`, in the project root. `17.ScriptforTestExperiment3.py` adds the root to
`PYTHONPATH` and runs every script from its own module folder. InVivo and
InSilico keep their intermediate files (`processed/`, and `simulations/` in
InSilico) in their own folder; every module writes a log to its own `logs/`
and its tables and figures to `results/<module>/`. A script run on its own
needs the root on `PYTHONPATH`:

```bash
# PowerShell, from the module folder
$env:PYTHONPATH = "<path to the project root>"
python S.BasalMatching.py
```

---

## Participants and data

17 participants from two datasets. Each real participant is paired with a
virtual patient of Py‑mgipsim by daily basal insulin. The pairs are listed in
`pairs.csv`, in the project root.

| Source | Participants | Availability |
|---|---|---|
| `zenodo` | 2301, 2304, 2307, 2308, 2309 | Public: T1D‑UOM dataset on Zenodo (CC BY 4.0) |
| `clinical` | Mann01–Mann12 | Available on reasonable request from the authors of the original clinical study; not redistributed here |

The five T1D‑UOM participants can be reproduced end to end from public data.
The clinical participants run through the same code once their exports are
available (see the data module).

---

## How to run

From the project root, in the pipeline environment:

```bash
python 17.ScriptforTestExperiment3.py demo                  # the whole pipeline on the demo data (see Demo)
python 17.ScriptforTestExperiment3.py                       # menu (modules 1-4; 5 = demo)
python 17.ScriptforTestExperiment3.py data                  # prepare raw/ (once, or when the input data change)
python 17.ScriptforTestExperiment3.py invivo                # one module, all participants
python 17.ScriptforTestExperiment3.py insilico Mann01 2308  # one module, only these participants
python 17.ScriptforTestExperiment3.py metrics
```

Two steps are run in the simulator environment, between the modules (see B):
the basal‑only simulation of each participant, and the simulation of the
before/after scenarios. Their files are kept in `simulator_runs/`, which the
pipeline reads but never modifies.

---

## Demo

```bash
python 17.ScriptforTestExperiment3.py demo
```

runs data → InVivo → InSilico → metrics for participant 2308 (public T1D‑UOM
data; the illustrative participant of the manuscript), with its Py‑mgipsim runs
included, so neither the clinical data nor the simulator are needed. Inputs are
read from `sample_data/` and every output goes to `demo_output/`; the files of
a full run are never touched. The data stage of the demo first rebuilds
`sample_data/` from `raw/2308/` and `simulator_runs/2308/` when they are present
(`data/S.GenerateSampleData.py`), otherwise it uses the `sample_data/` shipped with
the code, and then places the runs where InSilico and metrics read them
(`data/S.PrepareDemo.py`). The demo's tables and figures for 2308 match those
of the full run.

---

## 0) data (input data → raw/)

`python 17.ScriptforTestExperiment3.py data` prepares `raw/{id}/` for every participant in `pairs.csv`,
with four files in the T1D‑UOM format: `UoMGlucose{id}.csv` (`bg_ts`, `value`,
mmol/L), `UoMNutrition{id}.csv` (`meal_ts`, `carbs_g`), `UoMBolus{id}.csv`
(`bolus_ts`, `bolus_dose`) and `UoMBasal{id}.csv` (`basal_ts`, `basal_dose`,
`insulin_kind`). Time stamps are `dd/mm/yyyy hh:mm`.

| Script | What it does |
|---|---|
| `S.GetZenodoData.py` | T1D‑UOM participants: copies their files from an unzipped `ManchesterCSCoordinatedDiabetesStudy-*` folder in the project root, or downloads the pinned Zenodo record (checked against its MD5) into `data_cache/` |
| `S.ConvertClinicalData.py --to-raw` | Clinical participants: converts each export (`xt_…_man0NN_ol_sleep.txt`, one per participant, in `Sleep XT files/`) into the four files. Only the sections `Glucose_concentration`, `Enteral_bolus (meal)`, `Insulin_bolus` and `Insulin_infusion` are read; time stamps and values are copied as text. Meal entries with a negative carbohydrate value (corrections in the export) are dropped. `--check` writes to `converted/` and compares with existing files in `raw/` |
| `S.CleanRawData.py` | Drops blank rows and exact copies; in glucose, keeps the first record when one time stamp carries two values; in boluses, drops a bolus with the same dose as the previous one recorded within 15 minutes (a second record of the same bolus). The originals are kept in `raw/{id}/original/`, with a `cleaning_log.csv`; a file written again by the two scripts above (new input data) replaces the kept original, recognised by the checksum of the last cleaned file |

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

| # | Script | What it does |
|---|---|---|
| 1 | `0.GeneratorExamplesZenodo.py` | Splits glucose, meals, bolus and basal by day |
| 2–3 | `3.PivotGeneratorZenodo.py`, `3.PivotGeneratorBasalZenodo.py` | 1440‑minute grids for glucose and basal |
| 4 | `4.MealBolusDetectionZenodo.py` | Removes 6 h after each of the 4 largest meals (by CHO) per day, on the analysis days |
| 5 | `4.MergeBasalZenodo.py` | Merges daily basal files |
| 6 | `5.MergeBGCleanZenodo.py` | Merges meal‑free glucose of the analysis days |
| 7 | `5.FillGapsBasalZenodo.py` | Representative basal profile (mode per minute) |
| 8 | `6.SimulationBasalAutomatedZenodo.py` | Rayleigh insulin‑action curve of the basal profile |
| 9–11 | `6.SplitHoursZenodo.py`, `7.InterpolationBGHourlyZenodo.py`, `8.RelativeChangeZenodo.py` | Hourly files, short‑gap interpolation, hourly relative change |
| 12–13 | `9.BoxplotZenodo.py`, `10.PivotGeneratormediansZenodo.py` | Hourly medians over every analysis day, and reliability (1 low / 2 medium / 3 high) |
| 14–15 | `12.MergeRChBasalNoActZenodo.py`, `13.InterpolationRChZenodo.py` | Guide curve of relative change (`BGRChInt`): hours not of high reliability outside their 25th–75th percentile are set aside and interpolated, then a light smoothing spline |
| 16 | `0.InterpolationBGHourlyDataZenodo.py` | Absolute median BG curve (mmol/L) at 1‑minute resolution, the reference for the basal‑only simulation (median across the `BGValue*` day columns only) |
| 17 | `S.SaveReservedDays.py` | Saves the files of the two evaluation days to `processed/{id}/Days/` |

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

Then run the module (`python 17.ScriptforTestExperiment3.py insilico`). For each pair in
`pairs.csv`, `17.ScriptforTestoPy-mgipsimForEGPTest.py` cleans
`processed/{id}/`, rebuilds `simulations/{id}/` with the basal‑only run from
`simulator_runs/` and runs:
`0.GeneratorExamplesPy-mgipsimForEGPtest.py` → `3.PivotGeneratorZenodo.py` →
`5.MergeBGCompletePy-mgipsimTest.py` → `5.FillGapsBasalTest.py` →
`6.SimulationBasalAutomatedTest.py` → `6.SplitHoursTest.py` →
`7.InterpolationBGHourlyTest.py` → `8.RelativeChangeTest.py` →
`9.BoxplotTest.py` → `10.PivotGeneratormediansTest.py` →
`12.MergeRChBasalNoActTest.py` → `13.InterpolationRChTest.py` →
`14.SimulationBolusCHOPy-mgipsimTest.py` → `15.GeneratorFileToPy-mgipsimTest.py`
→ `S.BuildMealScenarios.py`.

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
  participant; also as a LaTeX table (`InputDescriptives_tables.tex`).
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
  (`PowerTestDescriptives.csv`, `PowerTestDescriptives_table.tex`) for the data
  appendix of the thesis.
- `G.Figures.py` — the figures of the manuscript, sized to be legible at the
  width at which they are printed; both days share the same axis limits.
- `G.CurveCheck.py` — per participant, the reconstructed and simulated curves
  with the hours coloured by reliability and the trimmed hours marked
  (`python G.CurveCheck.py <id>` for one participant, used while building a
  simulator input).
- `G.ScenarioPlot.py` — per participant, simulated glucose before and after
  the recommended basal on the two evaluation days, with the meals and the two
  basal profiles.

Outputs in `results/metrics/`:

| File | Manuscript |
|---|---|
| `tables/Table3_Day1.csv`, `tables/Table4_Day2.csv` | variability, excursion and composite stability per participant |
| `tables/Table5_Safety.csv` | bias, ±15% hours, lower‑variability hours, TIR and ΔInsulin |
| `tables/metrics_by_participant.csv` | all metrics, one row per participant and day |
| `tables/MealCoverage_*.csv` | meal coverage figures quoted in Methods and Limitations |
| `tables/CurveAgreement_*.csv` | agreement between reconstructed and simulated curves |
| `tables/TrimmingEffect_*.csv` | effect of the trimming on the guide curve |
| `tables/PowerAnalysisTest.csv` | paired t test on the SD (power analysis) |
| `tables/InputDescriptives_*.csv`, `tables/InputDescriptives_tables.tex` | CGM coverage of the analysis days (data appendix of the thesis) |
| `figures/Day1.png`, `figures/Day2.png` | hourly evaluation of participant 2308 |
| `figures/VariabilityDay1.png`, `…Day2.png` | SD before vs after |
| `figures/MeanDeviationDay1.png`, `…Day2.png` | ΔtaMAE per participant |
| `figures/CompositeStabilityDay1.png`, `…Day2.png` | composite stability index |
| `figures/CurveCheck_<id>.png`, `figures/Scenarios_<id>.png` | per‑participant checks (not in the manuscript) |

`G.TrimmedHoursCheck.py` (optional) confirms that the trimmed hours used by
`S.CurveAgreement.py` are those set aside by `13.InterpolationRChZenodo.py`.

---

## Environments

Two Python environments, kept separate; they communicate only through CSV and
JSON files.

| Environment | Python | Used by |
|---|---|---|
| Pipeline | 3.9.12 | InVivo, InSilico, metrics (`requirements.txt`, pinned) |
| Simulator | 3.12 | Py‑mgipsim (its own `requirements.txt`) |

```bash
# Pipeline
conda create -n pbt_test python=3.9.12
conda activate pbt_test
pip install -r requirements.txt

# Simulator (https://github.com/illinoistech-itm/py-mgipsim), in the project root
conda create -n mgipsim python=3.12
conda activate mgipsim
git clone https://github.com/illinoistech-itm/py-mgipsim.git
cd py-mgipsim
pip install -r requirements.txt
python interface_cli.py --help
```

The scripts read the virtual‑patient files from `py-mgipsim/` in the project
root. If Py‑mgipsim is installed elsewhere, set `PYMGIPSIM_PATIENTS` to its
`pymgipsim/VirtualPatient/Models/T1DM/ExtHovorka/Patients/` folder.

---

## Method parameters

The parameters shared by several steps are set once in `globals.py`:
`N_MEALS = 4` (largest meals per day, excluded in InVivo and simulated in the
scenarios), `MEAL_WINDOW_HOURS = 6` (glucose removed after each of them),
`LEAD_HOURS = 2` and `NEGATIVE_RATE_SHIFT_MIN = 120` (step 14), and
`MIN_HIGH_REL_HOURS = 6` (curve agreement). `ILLUSTRATIVE_ID = "2308"` sets the
participant of the illustrative figures.

---

## Units

Glucose is converted between mmol/L and mg/dL with the single factor
`MGDL_PER_MMOL = 18.0182`, set in `globals.py`.

---

## Reproducibility

Each run of InVivo and InSilico starts from a clean `processed/{id}/`, InSilico
rebuilds its working simulations from `simulator_runs/`, metrics uses a
simulator result only if it was simulated with the settings of the current
run, and rebuilds `results/metrics/` from scratch. The outputs therefore depend
only on the input data, the simulator results and the code.

To check that a change leaves the results unchanged, keep a copy of
`results/` and compare every table of the two runs:

```bash
python compare_results.py results_before results
```

---

## Citation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17467828.svg)](https://doi.org/10.5281/zenodo.17467828)

**Software (this repository):** Gasca García, D. *PBT — Paper 3 Pipeline
(v1.0.0)*. Zenodo. doi: 10.5281/zenodo.17467828

```bibtex
@software{gasca_garcia_pbt_paper3_2025_v1_0_0,
  author  = {Gasca García, Daniel},
  title   = {PBT — Paper 3 Pipeline},
  version = {v1.0.0},
  year    = {2025},
  doi     = {10.5281/zenodo.17467828},
  url     = {https://doi.org/10.5281/zenodo.17467828}
}
```

**Simulator:** py-mgipsim: An Open-Source Python Library for Simulating Type 1
Diabetes With Diverse Meals and Physical Activities. *J Diabetes Sci Technol.*
2025;19(3):855–856.

**Dataset (T1D‑UOM):** Alsuhaymi A, Bilal A, Gasca Garcia D, et al. *A
Longitudinal Multimodal Dataset of Type 1 Diabetes.* Scientific Data (2025).
doi:10.1038/s41597-025-05695-1 — data on Zenodo (V1.0.4), doi:10.5281/zenodo.17361905
(CC BY 4.0).

---

## License

MIT (see `LICENSE`).
