# InVivo — Composite-Day Construction & Basal Cues

This module builds composite-day glucose profiles at 1-minute resolution **after excluding post-prandial windows**, computes hourly **relative change**, and summarises **medians/outliers** to inform conservative basal redistribution. It also includes plots/medians/merges commonly run **after** the core generation to support later phases.

---

## 🔁 Execution Order (single list) 

1. `0.GeneratorExamplesZenodo.py` *(prepare per-day raw tables)*  
2. `4.MealBolusDetectionZenodo.py` *(mark post-prandial windows; top-4 meals/day)*  
3. `3.PivotGeneratorZenodo.py` *(timestamp pivot for BG)*  
4. `5.MergeBGCleanZenodo.py` *(merge BG → BGwNMLeftJoined<ID>.csv)*  
5. `0.InterpolationBGHourlyDataZenodo.py` *(hourly medians + 1‑min interpolation)*  
6. `3.PivotGeneratorBasalZenodo.py` *(timestamp pivot for basal)*  
7. `4.MergeBasalZenodo.py` *(multi‑day basal merge)*  
8. `5.FillGapsBasalZenodo.py` *(impute/mode → BasalImputed<ID>.csv)*  
9. `6.SimulationBasalAutomatedZenodo.py` *(basal action curve / Rayleigh‑like PD)*  
10. `6.SplitHoursZenodo.py` *(split BG by hours)*  
11. `7.InterpolationBGHourlyZenodo.py` *(hourly interpolation helper)*  
12. `8.RelativeChangeZenodo.py` *(hourly relative change)*  
13. `9.BoxplotZenodo.py` *(hourly boxplots)*  
14. `10.PivotGeneratormediansZenodo.py` *(robust hourly medians)*  
15. `12.MergeRChBasalNoActZenodo.py` *(merge relative change + basal)*  
16. `13.InterpolationRChZenodo.py` *(interpolate relative change)*  
17. `14.SimulationBolusCHOPy-mgipsimZenodo.py` *(meal/bolus sim helper)*  
18. `17.ScriptforTestZenodo.py` *(orchestrator wrapper)*  

> The flow above matches the files in this folder; steps **1–10** generate the core artefacts, while **11–18** add plots/medians/merges used by later stages.

---

## 📥 Inputs
- `globals.py` (IDs and paths: `id`, `id2`, `fileToSave`, `path`)
- Raw CSVs: CGM, basal, bolus, meals

## 📤 Key Outputs (examples)
- `BGwNMLeftJoined<ID>.csv`  
- `BGHourInterpolated<ID>*.csv`  
- `BasalImputed<ID>.csv` / `BasalSimulated<ID>.csv`  
- Hourly split/interpolated tables, medians, and relative‑change merges

---

## ▶️ Quick Start
```bash
# From repository root
pip install -r requirements.txt

# Verify globals (paths/IDs)
# globals.py: id, id2, fileToSave, path

# Run in order (example)
python InVivo/0.GeneratorExamplesZenodo.py
python InVivo/4.MealBolusDetectionZenodo.py
python InVivo/3.PivotGeneratorZenodo.py
python InVivo/5.MergeBGCleanZenodo.py
python InVivo/0.InterpolationBGHourlyDataZenodo.py
python InVivo/3.PivotGeneratorBasalZenodo.py
python InVivo/4.MergeBasalZenodo.py
python InVivo/5.FillGapsBasalZenodo.py
python InVivo/6.SimulationBasalAutomatedZenodo.py
python InVivo/6.SplitHoursZenodo.py
python InVivo/7.InterpolationBGHourlyZenodo.py
python InVivo/8.RelativeChangeZenodo.py
python InVivo/9.BoxplotZenodo.py
python InVivo/10.PivotGeneratormediansZenodo.py
python InVivo/12.MergeRChBasalNoActZenodo.py
python InVivo/13.InterpolationRChZenodo.py
python InVivo/14.SimulationBolusCHOPy-mgipsimZenodo.py
python InVivo/17.ScriptforTestZenodo.py
```

---

## 🧭 Notes
- Align timestamps (minute-level) for merges/pivots.
- Exclude post-prandial windows **before** computing hourly medians/relative change.
- Outputs are written under `fileToSave` (see `globals.py`).
