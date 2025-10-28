# Personalised Basal Tuner (PBT) — Experiment 3 (Recommender, In‑Silico)

Repository organised in **four modules** to reproduce the end‑to‑end flow of Experiment 3:  
**InVivo → InSilico → Meals → Metrics**. The goal is to recommend a **basal rate recommendations** and evaluate it **in‑silico** with Py‑mgipsim (2 days with meals).

---

## 📄 Context (Paper 4)

This pipeline accompanies the manuscript where PBT **generates basal rate recommendations** (changes to insulin basal profiles) and evaluates those recommendations **in‑silico** with Py‑mgipsim. Reported outcomes include improved composite stability, preserved safety (near‑zero bias; ISO ±15% compliance), and minimal change in total basal insulin. See **[docs/Paper4_Context.md](./docs/Paper4_Context.md)** for the scientific background, rationale, and result summaries.

---

## 📁 Folder structure

```
InVivo/      # Real‑data processing & signals for basal adjustment
InSilico/    # Py‑mgipsim simulations (2 days with meals)
Meals/       # “Before/After” meal & bolus scenarios
Metrics/     # Figures & KPIs (Boxplots → ISO ±15% → I, ΔtaMAE, STD, TIR, bias, Δinsulin)
globals.py   # IDs & paths (edit before running)
LICENSE  •  CITATION.cff  •  requirements.txt
```

---

## ▶️ Full execution order

### A) **InVivo** (real data → signals)
**Purpose:** build a 1‑min composite day excluding post‑prandial windows, compute hourly **relative change**, robust **medians/outliers**, and artefacts for basal rate recommendations.

**Scripts (in order):**
1. `0.GeneratorExamplesZenodo.py`  
2. `4.MealBolusDetectionZenodo.py`  
3. `3.PivotGeneratorZenodo.py`  
4. `5.MergeBGCleanZenodo.py`  
5. `0.InterpolationBGHourlyDataZenodo.py`  
6. `3.PivotGeneratorBasalZenodo.py`  
7. `4.MergeBasalZenodo.py`  
8. `5.FillGapsBasalZenodo.py`  
9. `6.SimulationBasalAutomatedZenodo.py`  
10. `6.SplitHoursZenodo.py`  
11. `7.InterpolationBGHourlyZenodo.py`  
12. `8.RelativeChangeZenodo.py`  
13. `9.BoxplotZenodo.py`  
14. `10.PivotGeneratormediansZenodo.py`  
15. `12.MergeRChBasalNoActZenodo.py`  
16. `13.InterpolationRChZenodo.py`  
17. `14.SimulationBolusCHOPy-mgipsimZenodo.py`  
18. `17.ScriptforTestZenodo.py` *(folder orchestrator)*

**Key outputs (examples):**
- `BGwNMLeftJoined<ID>.csv`, `BGHourInterpolated<ID>*.csv`  
- `BasalImputed<ID>.csv` / `BasalSimulated<ID>.csv`  
- Hourly tables, interpolations, and medians used by later phases

---

### B) **InSilico** (2‑day simulation with meals)
**Purpose:** evaluate the adjusted basal under realistic meal patterns using **Py‑mgipsim**.

**Scripts (in order):**
1. `0.GeneratorExamplesPy-mgipsimForEGPtest.py`  
2. `3.PivotGeneratorZenodo.py`  
3. `5.MergeBGCompletePy-mgipsimTest.py`  
4. `6.SplitHoursTest.py`  
5. `7.InterpolationBGHourlyTest.py`  
6. `8.RelativeChangeTest.py`  
7. `9.BoxplotTest.py`  
8. `10.PivotGeneratormediansTest.py`  
9. `12.MergeRChBasalNoActTest.py`  
10. `13.InterpolationRChTest.py`  
11. `14.SimulationBolusCHOPy-mgipsimTest.py` *(if required by your scenario)*  
12. `15.GeneratorFileToPy-mgipsimTest.py` *(writes updates back to `Simulation_{id2}`)*  
13. `5.FillGapsBasalTest.py` *(optional utility if your run needs it)*  
14. `6.SimulationBasalAutomatedTest.py` *(alternative helper, optional)*  
15. `17.ScriptforTestoPy-mgipsimForEGPTest.py` *(TEST orchestrator)*

**Expected inputs:**
- `work/.../Simulation_{id2}/simulation_settings.json` and `state_results.xlsx`  
- `BasalImputed{id2}.csv` if referenced by your steps

---

### C) **Meals** (before/after scenarios)
**Purpose:** inject **before/after** meals and boluses into simulation runs for robustness tests.

**Script:**
- `0.GeneratorBolusExamplesPy-mgipsimForEGPMealTest.py`  
  (can rename `Simulation_*` → `Simulation_{id}`, adjust `end_time`, and inject events using ICR/correction from `{path}/{id}.json`).

---

### D) **Metrics** (figures & KPIs)
**Required order:**
1. `0.BoxPlotsPerHour.py` → writes `hourly_mean_and_std.csv` (+ boxplot figures)  
2. *(If your ISO script needs XLSX, convert CSV → `hourly_mean_and_std.xlsx`)*  
3. `0.ISO.py` → ISO (±15% bias) figures reading the XLSX  
4. `0.Metrics.py` → final KPIs: **I**, **ΔtaMAE**, **STD**, **TIR**, **bias**, **Δinsulin**

**Typical inputs:** per‑minute “Before/After” Excel, `hourly_mean_and_std.xlsx`, and `DayN.xlsx` files.

---

## ⚙️ Requirements & install

- **Python ≥ 3.10**  
- Packages: `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `openpyxl`, `pyyaml`

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

**Configure** `globals.py` with `id`, `id2`, `fileToSave`, `path` (paths to your data/simulator).

---

## 🚀 Quick start

1) **InVivo** → run steps 1–18 in order (according to your dataset).  
2) Apply the **basal rate recommendations** (based on your artefacts/rules).  
3) **InSilico** → run steps 1–15 to evaluate the adjusted basal (2 days with meals).  
4) **Meals** → inject “before/after” scenarios if you want extra robustness tests.  
5) **Metrics** → generate ISO figures and final KPIs.

> Keep seeds/versions fixed for reproducibility. Check each folder’s `README.md` for CLI details and artefacts.

---

## 📥 Inputs / 📤 Outputs (summary)

- **Inputs:** real CGM/basal/bolus/meal logs (**InVivo**); Py‑mgipsim `Simulation_{id2}` folder (**InSilico**); per‑minute and per‑day Excel files (**Metrics**).  
- **Outputs:** intermediate CSV/XLSX (merges, interpolations, hourly splits), ISO figures, and KPIs (**I**, **ΔtaMAE**, **STD**, **TIR**, **bias**, **Δinsulin**).

---


---

## 📌 Citation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17467828.svg)](https://doi.org/10.5281/zenodo.17467828)

**Manuscript**: *Paper 4 — Basal Rate Recommendations evaluated in-silico with Py-mgipsim.*  
**Software (this repository)**: Gasca García, D. **PBT — Paper 4 Pipeline (v1.0.0)**. Zenodo/GitHub. DOI:https://doi.org/10.5281/zenodo.17467828

### BibTeX
```bibtex
@software{gasca_garcia_pbt_paper4_2025_v1_0_0,
  author  = {Gasca García, Daniel},
  title   = {PBT — Paper 4 Pipeline},
  version = {v1.0.0},
  year    = {2025},
  doi     = {10.5281/zenodo.17467828},
  url     = {https://doi.org/10.5281/zenodo.17467828}
} 
```

--- 

## 📝 License
MIT (see `LICENSE`).
