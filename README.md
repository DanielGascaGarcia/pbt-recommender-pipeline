# PBT — Paper 3 Pipeline (Recommender, In Silico)

Code of the article *Towards a Personalised Basal Tuner: Recommending Optimised
Basal Insulin Rates for Improved Glycaemic Control in Type 1 Diabetes*
(submitted to *Scientific Reports*). It produces every table and data figure
of the article.

- **Repository:** https://github.com/DanielGascaGarcia/pbt-recommender-pipeline
- **Implementation notes:** [`docs/NOTES.md`](docs/NOTES.md)
- **Licence:** MIT

---

## Contents

1. [Quick start](#quick-start)
2. [What it does](#what-it-does)
3. [Data](#data)
4. [Installation](#installation)
5. [Running](#running)
6. [Outputs](#outputs)
7. [Configuration](#configuration)
8. [Repository layout](#repository-layout)
9. [Reproducibility](#reproducibility)
10. [Citation](#citation)

---

## Quick start

Run the whole pipeline on the demo participant (public data, no simulator
needed):

```bash
conda create -n pbt_test python=3.9.12
conda activate pbt_test
pip install -r requirements.txt
python 17.ScriptforTestExperiment3.py demo
```

The results appear in `demo_output/`.

---

## What it does

The Personalised Basal Tuner (PBT) recommends hour‑by‑hour adjustments to a
basal insulin profile from real CGM and pump records. It evaluates them in
silico with Py‑mgipsim, on two simulated days with meals, before and after the
adjustment.

### Modules

The pipeline runs four modules, in this order:

1. **data** (`data/`) — prepares the input files of every participant in `raw/`.
2. **InVivo** (`InVivo/`) — from the real data: the composite day, its hourly relative change and reliability, the guide curve, the reference glucose curve, the evaluation days and the virtual‑patient matching.
3. **InSilico** (`InSilico/`) — the same steps on the basal‑only simulation of each participant; the recommended basal profile; the meal scenarios.
4. **metrics** (`metrics/`) — collects the simulated scenarios and computes the metrics, tables and figures.

### Method in brief

1. **Days.** Up to 45 days of CGM data per participant are analysis days; the next two are evaluation days.
2. **Meals.** Glucose within 6 h after each of the four largest meals of each analysis day is removed.
3. **Composite day.** A 24‑hour profile of the hourly relative change of glucose, with a three‑level reliability flag based on the number of contributing days.
4. **Guide curve.** Hours not of high reliability whose value falls outside the 25th–75th percentile are set aside (interquartile trimming) and interpolated, then lightly smoothed.
5. **Virtual patient.** Each participant is matched to a Py‑mgipsim patient by daily basal insulin; its basal‑only simulation is built to follow the participant's high‑reliability hours (a manual step, checked against a written agreement criterion).
6. **Recommendation.** Steps 3–4 are applied to the simulated day, and its deviations are flattened (insulin‑on‑board model, 2‑h lead).
7. **Evaluation.** The two evaluation days are simulated with their four largest meals and boluses, before and after the recommendation.

---

## Data

17 participants from two sources, each paired with a virtual patient of
Py‑mgipsim (`pairs.csv`).

- **T1D‑UOM** (2301, 2304, 2307, 2308, 2309) — public dataset on Zenodo, V1.0.4 (CC BY 4.0). Downloaded automatically by `data/S.GetZenodoData.py`.
- **Clinical** (Mann01–Mann12) — sensor‑augmented pump (open‑loop) period of a randomised crossover trial. Available on reasonable request from the authors of that study; not redistributed here. Converted by `data/S.ConvertClinicalData.py` once the exports are available.

The simulator inputs and outputs of all 17 participants are included in
`simulator_runs/`, so the metrics can be recomputed without running the
simulator.

---

## Installation

Two Python environments, kept separate. They communicate only through CSV and
JSON files.

- **Pipeline** — Python 3.9.12; runs data, InVivo, InSilico and metrics.
- **Simulator** — Python 3.12; runs [Py‑mgipsim](https://github.com/illinoistech-itm/py-mgipsim).

```bash
# Pipeline
conda create -n pbt_test python=3.9.12
conda activate pbt_test
pip install -r requirements.txt

# Simulator, cloned into the project root
conda create -n mgipsim python=3.12
conda activate mgipsim
git clone https://github.com/illinoistech-itm/py-mgipsim.git
cd py-mgipsim
pip install -r requirements.txt
```

> The scripts read the virtual‑patient files from `py-mgipsim/` in the project
> root. If Py‑mgipsim is installed elsewhere, set `PYMGIPSIM_PATIENTS` to its
> `pymgipsim/VirtualPatient/Models/T1DM/ExtHovorka/Patients/` folder.

---

## Running

### Commands

From the project root, in the pipeline environment:

```bash
python 17.ScriptforTestExperiment3.py                       # menu
python 17.ScriptforTestExperiment3.py demo                  # whole pipeline, demo participant
python 17.ScriptforTestExperiment3.py data                  # prepare raw/ (once)
python 17.ScriptforTestExperiment3.py invivo                # one module, all participants
python 17.ScriptforTestExperiment3.py insilico Mann01 2308  # one module, some participants
python 17.ScriptforTestExperiment3.py metrics
```

### Simulator steps

Two steps are run in the simulator environment, between modules:

1. **Before InSilico** — the basal‑only simulation of each participant.
2. **Before metrics** — the four scenarios of each participant (two days, before and after).

Their files are kept in `simulator_runs/`, which the pipeline reads but never
modifies. Details: [`docs/NOTES.md`](docs/NOTES.md#b-insilico-basal-recommendation-and-meal-scenarios).

### Demo

`demo` runs the four modules for participant 2308, the illustrative
participant of the article, with its simulator runs included.

- Inputs are read from `sample_data/`; every output goes to `demo_output/`.
- Neither the clinical data nor the simulator are needed.
- The files of a full run are never touched.
- The demo's tables and figures for 2308 match those of the full run.

### Running a single script

The launcher adds the project root to `PYTHONPATH`, so every script finds
`globals.py`. To run one script on its own, set it first, from the script's
module folder:

```bash
cd InVivo
$env:PYTHONPATH = "C:\path\to\the\project"   # PowerShell
# export PYTHONPATH=/path/to/the/project     # Linux / macOS
python S.BasalMatching.py
```

### Execution order

Each module has its own orchestrator, called by the launcher. The step‑by‑step
list is in [`docs/NOTES.md`](docs/NOTES.md).

- **data** — `S.GetZenodoData.py` → `S.ConvertClinicalData.py` → `S.CleanRawData.py`
- **InVivo** — `17.RunAllZenodo.py` (steps 0–13, reference curve, evaluation days) → `S.BasalMatching.py`
- **InSilico** — `17.ScriptforTestoPy-mgipsimForEGPTest.py` (steps 0–15 on the simulated day, then `S.BuildMealScenarios.py`)
- **metrics** — `S.SyncSimulatorResults.py` → `S.CollectScenarioResults.py` → descriptive tables (`S.MealCoverage.py`, `S.InputDescriptives.py`, `S.CurveAgreement.py`, `S.TrimmingEffect.py`) → `S.PowerAnalysisTest.py` → figures (`G.Figures.py`, `G.CurveCheck.py`, `G.ScenarioPlot.py`, `G.TrimmingEffect.py`)

---

## Outputs

Tables go to `results/<module>/tables/` and figures to
`results/<module>/figures/`. The code writes every table it computes; the
article reports a selection.

The tables of the full run are included in the repository, so every reported
value can be checked without re‑running the pipeline. Figures are not
versioned; they are regenerated by the code.

### Reported in the article

- **`invivo/tables/Table1_basal_matching.csv`** — daily basal and bolus of each participant and the virtual patient matched (Table 1).
- **`metrics/tables/Table3_Day1.csv`, `Table4_Day2.csv`** — variability, excursion and composite stability per participant (Tables 3 and 4).
- **`metrics/tables/Table5_Safety.csv`** — bias, hours within ±15%, lower‑variability hours, TIR and ΔInsulin (Table 5).
- **`metrics/tables/metrics_by_participant.csv`** — all metrics, one row per participant and day.
- **`metrics/tables/PowerAnalysisTest.csv`** — the planned one‑tailed paired *t* test on the SD, per day.
- **`metrics/tables/CurveAgreement_summary.csv`, `CurveAgreement_by_participant.csv`** — agreement between the reconstructed and simulated curves (criterion of the manual step).
- **`metrics/tables/MealCoverage_*.csv`** — meal coverage, quoted in Methods and Limitations.
- **`metrics/tables/TrimmingEffect_summary.csv`** — effect of the trimming on the guide curve, quoted in Methods.

### Additional analyses (data appendix of the thesis)

- **`metrics/tables/PowerTestDescriptives.csv`, `PowerTestDescriptives_table.tex`** — descriptive statistics of the variables of the planned test.
- **`metrics/tables/InputDescriptives_*.csv`, `InputDescriptives_tables.tex`** — CGM coverage of the analysis days.

### Diagnostic

- **`invivo/tables/RawDataCheck.csv`** — checks of the input files (`data/S.CheckRawData.py`, optional).
- **`metrics/tables/CurveAgreement_by_hour.csv`, `CurveAgreement_by_reliability.csv`** — curve agreement by hour and by reliability level.
- **`metrics/tables/TrimmingEffect_by_hour.csv`, `TrimmingEffect_by_participant.csv`** — effect of the trimming, in detail.
- **`metrics/tables/hourly_mean_and_std_<id>_Day<n>.csv`, `Day1.csv`, `Day2.csv`** — hourly values behind the evaluation figures.
- **`metrics/figures/CurveCheck_<id>.png`, `Scenarios_<id>.png`** — per‑participant checks.

### Figure map

- **Figure 1** (relative change, participant 2308) — `InVivo/12.MergeRChBasalNoActZenodo.py` → `invivo/figures/RelativeChange_2308.png`
- **Figure 2** (workflow diagram) — not generated by code
- **Figures 3–4** (evaluation of 2308, Days 1 and 2) — `metrics/G.Figures.py` → `Day1.png`, `Day2.png`
- **Figures 5 and 8** (SD before vs after) — `metrics/G.Figures.py` → `VariabilityDay1.png`, `VariabilityDay2.png`
- **Figures 6 and 9** (ΔtaMAE) — `metrics/G.Figures.py` → `MeanDeviationDay1.png`, `MeanDeviationDay2.png`
- **Figures 7 and 10** (composite stability index) — `metrics/G.Figures.py` → `CompositeStabilityDay1.png`, `CompositeStabilityDay2.png`
- **Table 2** (virtual patients) — parameters of Py‑mgipsim, not generated by code

---

## Configuration

`globals.py`, in the project root, holds the paths, the participants and the
parameters shared by several steps. Paths are resolved relative to it, so the
repository runs as cloned.

- **`PAIRS_FILE`** — `pairs.csv`: real participant → virtual patient, and the source of each.
- **`ZENODO_RECORD`** — Zenodo record of the T1D‑UOM version used (V1.0.4).
- **`MAX_ANALYSIS_DAYS`, `RESERVED_DAYS`** — 45 analysis days and 2 evaluation days.
- **`N_MEALS`, `MEAL_WINDOW_HOURS`** — the 4 largest meals per day, and the 6‑h window removed after each.
- **`LEAD_HOURS`, `NEGATIVE_RATE_SHIFT_MIN`** — placement of each basal correction (2 h before), and handling of reductions larger than the rate.
- **`MIN_HIGH_REL_HOURS`** — minimum high‑reliability hours to centre the curves in the agreement check.
- **`ILLUSTRATIVE_ID`** — participant of the illustrative figures (2308).
- **`MGDL_PER_MMOL`** — unit conversion factor (18.0182).
- **`FIGURE_TITLES`** — `False` for submission figures; `True` to render titles for local review.
- **`DEMO`** — set by the launcher in demo mode.

---

## Repository layout

```
pbt-recommender-pipeline/
├─ 17.ScriptforTestExperiment3.py   launcher
├─ globals.py                       configuration
├─ pairs.csv                        real participant → virtual patient
├─ data/                            input data: download, conversion, cleaning, checks
├─ InVivo/                          real data → composite day, guide curve, matching
├─ InSilico/                        simulated day → recommendation, meal scenarios
├─ metrics/                         metrics, tables and figures
├─ simulator_runs/                  simulator inputs and outputs of every participant
├─ sample_data/                     demo input (participant 2308)
├─ docs/NOTES.md                    implementation notes
├─ compare_results.py               compares every table of two runs
├─ results/<module>/tables/         tables of the full run (versioned)
└─ requirements.txt · CITATION.cff · RELEASE_NOTES.md · LICENSE
```

Created by the code and not distributed (listed in `.gitignore`): `raw/`,
`results/<module>/figures/`, `processed/`, `logs/`, `demo_output/`,
`InSilico/simulations/`.
The simulator (`py-mgipsim/`) is cloned separately.

---

## Reproducibility

Every run starts from a clean state:

- InVivo and InSilico clear their intermediate files.
- InSilico rebuilds its working simulations from `simulator_runs/`.
- metrics uses a simulator result only if it was simulated with the settings of the current run, and rebuilds its results from scratch.

The outputs therefore depend only on the input data, the simulator results and
the code. To check that a change leaves the results unchanged, keep a copy of
`results/` and compare every table of the two runs:

```bash
python compare_results.py results_before results
```

---

## Citation

**Article**

> Gasca Garcia D, Thabit H, Nutter PW, Harper S. Towards a Personalised Basal
> Tuner: Recommending Optimised Basal Insulin Rates for Improved Glycaemic
> Control in Type 1 Diabetes. Submitted to *Scientific Reports*.

**Software** (concept DOI: always resolves to the latest version; see `CITATION.cff`)

> Gasca García D. *PBT — Paper 3 Pipeline* [Computer software]. Zenodo.
> doi:CONCEPT_DOI

```bibtex
@software{gasca_garcia_pbt_paper3,
  author  = {Gasca García, Daniel},
  title   = {PBT — Paper 3 Pipeline},
  year    = {2026},
  doi     = {CONCEPT_DOI},
  url     = {https://doi.org/CONCEPT_DOI}
}
```

**Simulator**

> Rashid M, Cinar A. py-mgipsim: An open-source Python library for simulating
> type 1 diabetes with diverse meals and physical activities. *J Diabetes Sci
> Technol.* 2025. doi:10.1177/19322968251328664

**Dataset (T1D‑UOM)**

> Alsuhaymi A, Bilal A, Gasca Garcia D, et al. A Longitudinal Multimodal
> Dataset of Type 1 Diabetes. *Scientific Data.* 2025.
> doi:10.1038/s41597-025-05695-1. Data on Zenodo (V1.0.4):
> doi:10.5281/zenodo.17361905 (CC BY 4.0).

**Related deposits** (concept DOIs)

- Paper 1 pipeline — 10.5281/zenodo.17392920
- Paper 2 pipeline — 10.5281/zenodo.17393514
- Software compendium — 10.5281/zenodo.17675141

---

## Licence

MIT. See `LICENSE`.
