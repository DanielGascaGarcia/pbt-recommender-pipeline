# InSilico — Basal Rate **Recommendations** with Py‑mgipsim (2‑Day with Meals)

This module **generates and evaluates basal insulin rate recommendations** using **Py‑mgipsim**.
It reads your `Simulation_{id2}` folder (settings + state results), builds merged BG tables, splits/interpolates by hour,
computes **relative change**, and produces plots/medians used by Metrics.

---

## 🔁 Execution Order (single list)

1. `0.GeneratorExamplesPy-mgipsimForEGPtest.py` — prepare per-day simulation outputs from `Simulation_{id2}`.
2. `3.PivotGeneratorZenodo.py` — pivot timestamps for BG tables.
3. `5.MergeBGCompletePy-mgipsimTest.py` — build complete merged BG from simulation outputs.
4. `6.SplitHoursTest.py` — split BG by hour.
5. `7.InterpolationBGHourlyTest.py` — per-hour interpolation helper.
6. `8.RelativeChangeTest.py` — compute hourly **relative change** for evaluation.
7. `9.BoxplotTest.py` — hourly boxplots from simulation.
8. `10.PivotGeneratorMediansTest.py` — robust hourly medians.
9. `12.MergeRChBasalNoActTest.py` — merge relative change with basal (no activity).
10. `13.InterpolationRChTest.py` — interpolate relative-change series for summaries.
11. `14.SimulationBolusCHOPy-mgipsimTest.py` — helper to simulate CHO/bolus scenarios if required.
12. `15.GeneratorFileToPy-mgipsimTest.py` — write updated files back into `Simulation_{id2}` (e.g., `simulation_settings.json`).
13. `5.FillGapsBasalTest.py` — utility for basal gap filling (use only if your run needs it).
14. `6.SimulationBasalAutomatedTest.py` — alternative/aux basal simulation helper (optional depending on flow).
15. `17.ScriptforTestoPy-mgipsimForEGPTest.py` — **orchestrator** wrapper for the TEST pipeline.

> The order above matches the files in this folder; items 11–14 are optional helpers depending on your scenario.

---

## 📥 Inputs
- `globals.py` (IDs/paths: `id`, `id2`, `fileToSave`, `path`).
- `work/.../Simulation_{id2}/simulation_settings.json` and `state_results.xlsx`.
- If using meals/boluses helpers, `{path}/{id2}.json` with carb ratio/correction (as required by your scripts).

## 📤 Key Outputs
- **Basal rate recommendation** file(s) (e.g., CSV) per participant.
- Merged BG tables (per-minute and per-hour), hourly splits, interpolations.
- Hourly boxplots and medians; relative-change tables for **Metrics**.

---

## ▶️ Quick Start
```bash
# From repository root
pip install -r requirements.txt

# Verify globals (paths/IDs)
# globals.py: id, id2, fileToSave, path

# Run in order
python InSilico/0.GeneratorExamplesPy-mgipsimForEGPtest.py
python InSilico/3.PivotGeneratorZenodo.py
python InSilico/5.MergeBGCompletePy-mgipsimTest.py
python InSilico/6.SplitHoursTest.py
python InSilico/7.InterpolationBGHourlyTest.py
python InSilico/8.RelativeChangeTest.py
python InSilico/9.BoxplotTest.py
python InSilico/10.PivotGeneratormediansTest.py
python InSilico/12.MergeRChBasalNoActTest.py
python InSilico/13.InterpolationRChTest.py
# Optional helpers
python InSilico/14.SimulationBolusCHOPy-mgipsimTest.py
python InSilico/15.GeneratorFileToPy-mgipsimTest.py
python InSilico/5.FillGapsBasalTest.py
python InSilico/6.SimulationBasalAutomatedTest.py

# Orchestrator (TEST)
python InSilico/17.ScriptforTestoPy-mgipsimForEGPTest.py
```

---

## 🧭 Notes
- Keep simulation seeds/versions fixed for reproducibility.
- Ensure `Simulation_{id2}` exists (baseline run), then **generate recommendations** and evaluate them with meals.
- Output paths are governed by `fileToSave` in `globals.py`.
