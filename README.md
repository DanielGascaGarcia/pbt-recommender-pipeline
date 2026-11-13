# PBT — Paper 3 Pipeline (Recommender, In Silico)

**Article:** *Towards a Personalised Basal Tuner: Recommending Optimised Basal
Insulin Rates for Improved Glycaemic Control in Type 1 Diabetes.* Submitted to
*Scientific Reports*.

**Repository:** https://github.com/DanielGascaGarcia/pbt-recommender-pipeline

This code produces every table and data figure of the article. A single
launcher runs the four modules in order.

---

## What it does

The Personalised Basal Tuner (PBT) recommends hour‑by‑hour adjustments to a
basal insulin profile from real CGM and pump records, and evaluates them in
silico with Py‑mgipsim, on two simulated days with meals, before and after the
adjustment.

The pipeline is organised in four modules, run in this order:

- **data** (`data/`) — prepares the input files of every participant in `raw/`
- **InVivo** (`InVivo/`) — builds the composite day from real data, its hourly relative change and reliability, the guide curve, the reference glucose curve, the evaluation days and the virtual‑patient matching
- **InSilico** (`InSilico/`) — applies the same steps to the basal‑only simulation of each participant, computes the recommended basal profile, and writes the meal scenarios
- **metrics** (`metrics/`) — collects the simulated scenarios and computes the metrics, tables and figures

**Method in brief**

1. For each participant, take up to 45 days of CGM data as analysis days and the next two as evaluation days.
2. Remove the glucose within 6 h after each of the four largest meals of each analysis day.
3. Build a 24‑hour composite day and compute the hourly relative change of glucose, with a three‑level reliability flag based on the number of contributing days.
4. Build the guide curve: hours not of high reliability whose value falls outside the 25th–75th percentile are set aside (interquartile trimming) and interpolated, then lightly smoothed.
5. Match each participant to a virtual patient of Py‑mgipsim by daily basal insulin, and build its basal‑only simulation to follow the participant's high‑reliability hours (a manual step, checked against a written agreement criterion).
6. Apply steps 3–4 to the simulated day and compute the recommended basal profile by flattening its deviations (insulin‑on‑board model, 2‑h lead).
7. Simulate the two evaluation days, with their four largest meals and boluses, before and after the recommendation, and compute the metrics.

Further technical detail of every step, including the data cleaning, the day
rule, the trimming, the manual simulator step and the flattening, is in
[`docs/NOTES.md`](docs/NOTES.md).

---

## Data

17 participants from two datasets, each paired with a virtual patient of
Py‑mgipsim. The pairs are listed in `pairs.csv`.

- **`zenodo`** (2301, 2304, 2307, 2308, 2309) — Public: T1D‑UOM dataset, Zenodo V1.0.4 (CC BY 4.0)
- **`clinical`** (Mann01–Mann12) — Sensor‑augmented pump (open‑loop) period of a randomised crossover trial; available on reasonable request from the authors of that study, not redistributed here

What can be reproduced:

- The five T1D‑UOM participants can be reproduced end to end from public data: the data module downloads them (`data/S.GetZenodoData.py`).
- The clinical participants run through the same code once their exports are available (`data/S.ConvertClinicalData.py`).
- The simulator inputs and outputs of all 17 participants are included in `simulator_runs/`, so the metrics can be recomputed without running the simulator.

---

## Installation

Two Python environments, kept separate; they communicate only through CSV and
JSON files.

- **Pipeline** (3.9.12) — data, InVivo, InSilico, metrics (`requirements.txt`, pinned)
- **Simulator** (3.12) — Py‑mgipsim (its own `requirements.txt`)

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
```

The scripts read the virtual‑patient files from `py-mgipsim/` in the project
root. If Py‑mgipsim is installed elsewhere, set `PYMGIPSIM_PATIENTS` to its
`pymgipsim/VirtualPatient/Models/T1DM/ExtHovorka/Patients/` folder.

---

## Running

From the project root, in the pipeline environment:

```bash
python 17.ScriptforTestExperiment3.py demo                  # whole pipeline on the demo data
python 17.ScriptforTestExperiment3.py                       # menu (modules 1-4; 5 = demo)
python 17.ScriptforTestExperiment3.py data                  # prepare raw/ (once, or when the input data change)
python 17.ScriptforTestExperiment3.py invivo                # one module, all participants
python 17.ScriptforTestExperiment3.py insilico Mann01 2308  # one module, only these participants
python 17.ScriptforTestExperiment3.py metrics
```

**Simulator steps.** Two steps are run in the simulator environment, between
the modules: the basal‑only simulation of each participant (before InSilico)
and the simulation of the four before/after scenarios (before metrics). Their
files are kept in `simulator_runs/`, which the pipeline reads but never
modifies. See [`docs/NOTES.md`](docs/NOTES.md#b-insilico-basal-recommendation-and-meal-scenarios).

**Demo.** `python 17.ScriptforTestExperiment3.py demo` runs the four modules
for participant 2308 (public data; the illustrative participant of the
article) with its simulator runs included, so neither the clinical data nor
the simulator are needed. Inputs are read from `sample_data/` and every output
goes to `demo_output/`; the files of a full run are never touched. The demo's
tables and figures for 2308 match those of the full run.

**Single scripts.** The launcher adds the project root to `PYTHONPATH`, so
every script finds `globals.py`. To run one script on its own, set it first,
from the script's module folder:

```bash
cd InVivo
$env:PYTHONPATH = "C:\path\to\the\project"   # PowerShell; Linux/macOS: export PYTHONPATH=/path/to/the/project
python S.BasalMatching.py
```

### Execution order

Each module has its own orchestrator, called by the launcher; the full list of
steps, with what each does, is in [`docs/NOTES.md`](docs/NOTES.md).

- **data** — `S.GetZenodoData.py`, `S.ConvertClinicalData.py`, `S.CleanRawData.py`
- **InVivo** — `17.RunAllZenodo.py` (steps 0–13, reference curve, evaluation days), then `S.BasalMatching.py`
- **InSilico** — `17.ScriptforTestoPy-mgipsimForEGPTest.py` (steps 0–15 on the simulated day, and `S.BuildMealScenarios.py`)
- **metrics** — `S.SyncSimulatorResults.py`, `S.CollectScenarioResults.py`, `S.MealCoverage.py`, `S.InputDescriptives.py`, `S.CurveAgreement.py`, `S.TrimmingEffect.py`, `S.PowerAnalysisTest.py`, `G.Figures.py`, `G.CurveCheck.py`, `G.ScenarioPlot.py`, `G.TrimmingEffect.py`

---

## Outputs

Tables are written to `results/<module>/tables/` and figures to
`results/<module>/figures/`. The package writes every table the code computes;
the article reports a selection. Each file is listed here with the use it has.

**Reported in the article**

- **`invivo/tables/Table1_basal_matching.csv`** — daily basal and bolus of each participant and the virtual patient matched (Table 1)
- **`metrics/tables/Table3_Day1.csv`, `Table4_Day2.csv`** — variability, excursion and composite stability per participant (Tables 3 and 4)
- **`metrics/tables/Table5_Safety.csv`** — bias, hours within ±15%, lower‑variability hours, TIR and ΔInsulin (Table 5)
- **`metrics/tables/metrics_by_participant.csv`** — all metrics, one row per participant and day
- **`metrics/tables/PowerAnalysisTest.csv`** — the planned one‑tailed paired *t* test on the SD, per day
- **`metrics/tables/CurveAgreement_summary.csv`, `CurveAgreement_by_participant.csv`** — agreement between the reconstructed and simulated curves (the criterion of the manual step)
- **`metrics/tables/MealCoverage_*.csv`** — meal coverage values quoted in Methods and Limitations
- **`metrics/tables/TrimmingEffect_summary.csv`** — effect of the trimming on the guide curve, quoted in Methods

**Additional analyses, not reported in the article** (data appendix of the thesis)

- **`metrics/tables/PowerTestDescriptives.csv`, `PowerTestDescriptives_table.tex`** — descriptive statistics of the variables of the planned test
- **`metrics/tables/InputDescriptives_*.csv`, `InputDescriptives_tables.tex`** — CGM coverage of the analysis days

**Diagnostic**

- **`invivo/tables/RawDataCheck.csv`** — checks of the input files (`data/S.CheckRawData.py`, optional)
- **`metrics/tables/CurveAgreement_by_hour.csv`, `CurveAgreement_by_reliability.csv`** — agreement by hour and by reliability
- **`metrics/tables/TrimmingEffect_by_hour.csv`, `TrimmingEffect_by_participant.csv`** — effect of the trimming, in detail
- **`metrics/tables/hourly_mean_and_std_<id>_Day<n>.csv`, `Day1.csv`, `Day2.csv`** — hourly values behind the evaluation figures
- **`metrics/figures/CurveCheck_<id>.png`, `Scenarios_<id>.png`** — per‑participant checks

### Figure map

- **Figure 1 (relative change of participant 2308)** — `InVivo/12.MergeRChBasalNoActZenodo.py` → `invivo/figures/RelativeChange_2308.png`
- **Figure 2 (workflow diagram)** — not generated by code
- **Figures 3 and 4 (evaluation of participant 2308, Days 1 and 2)** — `metrics/G.Figures.py` → `Day1.png`, `Day2.png`
- **Figures 5 and 8 (SD before vs after)** — `metrics/G.Figures.py` → `VariabilityDay1.png`, `VariabilityDay2.png`
- **Figures 6 and 9 (ΔtaMAE)** — `metrics/G.Figures.py` → `MeanDeviationDay1.png`, `MeanDeviationDay2.png`
- **Figures 7 and 10 (composite stability index)** — `metrics/G.Figures.py` → `CompositeStabilityDay1.png`, `CompositeStabilityDay2.png`
- **Table 2 (virtual patients)** — parameters of Py‑mgipsim, not generated by code

---

## Configuration

`globals.py`, in the project root, holds the paths, the participants and the
parameters shared by several steps. Paths are resolved relative to it, so the
repository runs as cloned.

- **`PAIRS_FILE`** — `pairs.csv`: real participant → virtual patient, and the source of each participant
- **`ZENODO_RECORD`** — Zenodo record of the T1D‑UOM dataset version (V1.0.4)
- **`MAX_ANALYSIS_DAYS`, `RESERVED_DAYS`** — up to 45 analysis days, and two evaluation days
- **`N_MEALS`, `MEAL_WINDOW_HOURS`** — the four largest meals per day, and the 6‑h window removed after each
- **`LEAD_HOURS`, `NEGATIVE_RATE_SHIFT_MIN`** — placement of each basal correction (2 h before), and handling of reductions larger than the rate
- **`MIN_HIGH_REL_HOURS`** — minimum high‑reliability hours to centre the curves in the agreement check
- **`ILLUSTRATIVE_ID`** — participant of the illustrative figures (2308)
- **`MGDL_PER_MMOL`** — unit conversion factor (18.0182)
- **`FIGURE_TITLES`** — `False` for submission figures; `True` to render titles for local review
- **`DEMO`** — set by the launcher in demo mode; all inputs from `sample_data/`, all outputs to `demo_output/`

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
├─ requirements.txt  •  CITATION.cff  •  RELEASE_NOTES.md  •  LICENSE
├─ raw/                             input data (created by the data module; not distributed)
├─ py-mgipsim/                      the simulator (cloned separately; not distributed)
└─ results/                         tables and figures (created by the code)
```

`raw/`, `results/`, `processed/`, `logs/`, `demo_output/` and
`InSilico/simulations/` are created by the code and are listed in
`.gitignore`.

---

## Reproducibility

Each run starts from a clean state: InVivo and InSilico clear their
intermediate files, InSilico rebuilds its working simulations from
`simulator_runs/`, metrics uses a simulator result only if it was simulated
with the settings of the current run, and rebuilds its results from scratch.
The outputs therefore depend only on the input data, the simulator results and
the code.

To check that a change leaves the results unchanged, keep a copy of `results/`
and compare every table of the two runs:

```bash
python compare_results.py results_before results
```

---

## Citation

**Article:** Gasca Garcia D, Thabit H, Nutter PW, Harper S. Towards a
Personalised Basal Tuner: Recommending Optimised Basal Insulin Rates for
Improved Glycaemic Control in Type 1 Diabetes. Submitted to *Scientific
Reports*.

**Software:** Gasca García D. *PBT — Paper 3 Pipeline* [Computer software].
Zenodo. doi: **CONCEPT_DOI**

The DOI above is the concept DOI: it always resolves to the most recent version.
See `CITATION.cff`.

```bibtex
@software{gasca_garcia_pbt_paper3,
  author  = {Gasca García, Daniel},
  title   = {PBT — Paper 3 Pipeline},
  year    = {2026},
  doi     = {CONCEPT_DOI},
  url     = {https://doi.org/CONCEPT_DOI}
}
```

**Simulator:** Rashid M, Cinar A. py-mgipsim: An open-source Python library for
simulating type 1 diabetes with diverse meals and physical activities.
*J Diabetes Sci Technol.* 2025. doi:10.1177/19322968251328664

**Dataset (T1D‑UOM):** Alsuhaymi A, Bilal A, Gasca Garcia D, et al. A
Longitudinal Multimodal Dataset of Type 1 Diabetes. *Scientific Data.* 2025.
doi:10.1038/s41597-025-05695-1 — data on Zenodo (V1.0.4),
doi:10.5281/zenodo.17361905 (CC BY 4.0).

Related deposits, by concept DOI:

- Paper 1 pipeline — 10.5281/zenodo.17392920
- Paper 2 pipeline — 10.5281/zenodo.17393514
- Software compendium — 10.5281/zenodo.17675141

---

## License

MIT. See `LICENSE`.
