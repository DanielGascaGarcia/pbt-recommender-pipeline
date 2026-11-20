# Release notes — PBT, Paper 3 Pipeline

DOI (this version): assigned on publication.
Previous version: PBT_recommender_v1.0.2 (doi: 10.5281/zenodo.18509612).

This release reorganises the code and adds the steps that prepare the input
data, so that every table and figure of the current version of the manuscript
is produced from the original data exports by the code.

## Structure

- One `globals.py`, in the project root, used by every module; `pairs.csv`
  moves to the root.
- New `data` module (`python 17.ScriptforTestExperiment3.py data`), run before InVivo:
  - `S.GetZenodoData.py`: T1D‑UOM participants (moved from InVivo).
  - `S.ConvertClinicalData.py`: converts the clinical exports into the
    T1D‑UOM file format. Meal entries with a negative carbohydrate value are
    dropped. On the original data it reproduces the files previously prepared
    for the study (48 of 48 files identical).
  - `S.CleanRawData.py`: removes blank rows, exact copies, glucose records
    that repeat a time stamp, and bolus records that repeat the previous bolus
    within 15 minutes. Originals are kept, with a log.
  - `S.CheckRawData.py`: format and range report of the input files.
- Simulator files are kept in `simulator_runs/`, which the pipeline never
  modifies; `InSilico/simulations/` becomes a working copy rebuilt on every run.
  The first step of metrics, `S.SyncSimulatorResults.py`, uses a scenario
  result only when the settings it was simulated with match those of the
  current run.
- Demo mode: `python 17.ScriptforTestExperiment3.py demo` runs the whole pipeline on participant 2308
  (public data) with its simulator runs included, from `sample_data/` to
  `demo_output/` (`data/S.GenerateSampleData.py`, `data/S.PrepareDemo.py`).
- `compare_results.py`: compares every table of two runs.

## Changes that affect reported values

- Timing of the recommended corrections (`14.SimulationBolusCHOPy-mgipsimTest.py`):
  each correction was sized assuming delivery 2 h before the deviation but was
  placed in the hour of the deviation; it is now placed 2 h earlier
  (`LEAD_HOURS = 2`), consistently with how it is sized.
- Rates bounded at zero: when a recommended reduction was larger than the rate,
  the remaining reduction was added 2 h earlier; it is now subtracted there,
  bounded at zero.
- Matching: participant 2301 is paired with the virtual patient selected by the
  daily basal rule (Patient_5).
- Reference curve (`0.InterpolationBGHourlyDataZenodo.py`): the column of the
  saved index (`Unnamed: 0`) entered the across‑day median as if it were one
  more day. In hours with data on 0–1 days the median exceeded 30, was
  discarded and was filled by interpolation, so the reference curve was
  smoothed there. Only the `BGValue*` day columns are now used. This changes
  the reference curve and its agreement with the basal‑only simulation; it
  does not change the recommendation, the guide curve or any before/after
  result.
- Simulator inputs: the basal‑only inputs of nine participants were rebuilt so
  that every participant meets the same operational criterion of agreement
  with its reconstructed curve: Pearson r ≥ 0.5 over the hours the guide keeps
  (hours with BG data that were not set aside when the guide was built), and a
  centred mean absolute difference below 1 mmol/L in high‑reliability hours.
  Five (2301, Man06, Man07, Man11, 2307) were rebuilt first; four more (Man01,
  Man02, Man09, Man10) after the reference curve was corrected. The input of
  Man07, which met the criterion with the largest difference in
  high‑reliability hours (0.87 mmol/L), was then refined further (0.45 mmol/L;
  r 0.68); the results use the refined input. The 68 scenarios were
  simulated again with the final inputs.

- Table 1: the daily basal and bolus of every participant are computed by
  `S.BasalMatching.py` (median of the daily totals), which now also reports
  the daily bolus.
- `9.BoxplotZenodo.py` includes every analysis day in the hourly medians of the
  guide curve (the largest change in any hourly median is below 0.3 mmol/L, and
  no reliability flag changes). `9.BoxplotTest.py` uses the same rule; with the
  single simulated day its output is unchanged.

## New outputs

- `metrics/S.MealCoverage.py`: coverage of the four‑largest‑meals rule and
  share of retained readings near meals not excluded or on days without meal
  records.
- `metrics/S.CurveAgreement.py`: agreement between the reconstructed curves
  and the basal‑only simulations, overall, in high‑reliability hours and by
  reliability.
- `metrics/G.CurveCheck.py` and `metrics/G.ScenarioPlot.py`: per‑participant
  figures of the curve agreement and of the before/after scenarios.
- `metrics/S.TrimmingEffect.py` and `metrics/G.TrimmingEffect.py`: how much the
  trimming of low‑reliability hours (`13.InterpolationRChZenodo.py`) changes
  the guide curve. In silico, the single basal‑only day makes every hour of
  high reliability, so no hour is trimmed there.
- `metrics/S.PowerAnalysisTest.py`: the one‑tailed paired t test of the power
  analysis on the SD before and after, per day, with its 95% CI, observed dz,
  Shapiro–Wilk, Wilcoxon and Bonferroni checks.
- `metrics/G.TrimmedHoursCheck.py`: checks that the trimmed hours match those
  of the guide construction.
- `metrics/S.InputDescriptives.py`: CGM coverage of the analysis days per
  participant, for the data appendix of the thesis chapter, also as a LaTeX
  table.
- Figure 1 of the manuscript: `InVivo/12.MergeRChBasalNoActZenodo.py` now saves
  the figure of the illustrative participant (`ILLUSTRATIVE_ID`, 2308) to
  `results/invivo/figures/`; it was previously only shown on screen.

## Other changes

- Figures (`metrics/G.Figures.py`): sized and with a font size that stay legible
  once scaled to the text width; the two days share the same axis limits; the
  hourly figures label their panels (a), (b), (c), and their percentage axis
  ends at 100%. The values drawn do not change.
- `S.PowerAnalysisTest.py` skips the test with fewer than 3 participants (as in
  the demo) and reports only the SDs; it also writes mean (SD), median (Q1–Q3)
  and range of the variables of the test, for the data appendix of the thesis
  (`PowerTestDescriptives.csv`, `PowerTestDescriptives_table.tex`).

- Method parameters are set once in `globals.py` and read by every script
  that uses them: `N_MEALS` (4), `MEAL_WINDOW_HOURS` (6), `LEAD_HOURS` (2),
  `NEGATIVE_RATE_SHIFT_MIN` (120) and `MIN_HIGH_REL_HOURS` (6). Same values
  as before; the outputs do not change.
- Glucose unit conversion uses one constant, `MGDL_PER_MMOL = 18.0182`, in
  `globals.py`; the Zenodo record of the dataset, `ZENODO_RECORD`, is also set
  there, together with the locations of the simulator runs and the working
  simulations (`simulator_runs_root`, `sims_root`), which every module uses.

- Code documentation: every script has a header in the format of the papers 1
  and 2 packages (what it does, inputs, outputs, notes, usage) and comments in
  English.

## Reproducibility

Every module starts from a clean state. A full run (`data`, `invivo`,
`insilico`, `metrics`) reproduces the tables of the manuscript; two runs give
identical tables. A run from a fresh clone, in a new environment, reproduced
all 57 tables of `results/`.

Py‑mgipsim version used for the results: commit `b985f8c` (25 February 2026),
pinned in the README; its virtual‑patient files give the daily basal used for
the matching and the correction factor used for the recommendation.

## License

MIT (see `LICENSE`).
