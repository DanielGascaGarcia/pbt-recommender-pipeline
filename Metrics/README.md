# Metrics — Figures & KPIs 

This module generates hourly **boxplots**, ISO ±15% figures, and final KPIs (**I**, **ΔtaMAE**, **STD**, **TIR**, **bias**, **Δinsulin**).

---

## 🔁 Execution Order

1. `0.BoxPlotsPerHour.py` → produces `hourly_mean_and_std.csv` (and boxplot figures).  
2. *(Adapter CSV→XLSX if needed)* → save as `hourly_mean_and_std.xlsx`.  
3. `0.ISO.py` → reads `hourly_mean_and_std.xlsx` and outputs ISO-style figures (bias ±15%).  
4. `0.Metrics.py` → computes KPIs from day-level files (e.g., `Day1.xlsx`, `Day2.xlsx`).

---

## 📥 Inputs
- Per-minute Excel for “before/after” profiles (path configured in `globals.py`, e.g., `BeforeAfterPerMinute.xlsx`).  
- `hourly_mean_and_std.xlsx` (or let step 1 create CSV and convert it to XLSX).  
- Day-level files for metric computation (e.g., `Day1.xlsx`, `Day2.xlsx`).  
- `globals.py` with `folder_path`/`file_path`/`file_name` as required by your scripts.

## 📤 Outputs
- `hourly_mean_and_std.csv` and `hourly_mean_and_std.xlsx`.  
- ISO figures (PNG/PDF depending on your script).  
- Final KPIs printed/saved by `0.Metrics.py` (tables/figures).

---

## ▶️ Quick Start
```bash
# From repository root
pip install -r requirements.txt

# Verify globals (paths/IDs)
# globals.py should define the paths consumed by your metrics scripts

# Run
python Metrics/0.BoxPlotsPerHour.py
# Convert CSV -> XLSX if your ISO script expects XLSX
python Metrics/0.ISO.py
python Metrics/0.Metrics.py
```

---

## 🧭 Notes
- Keep unit consistency (mmol/L vs mg/dL) between steps if you export/import external files.
- Ensure day-level files contain the expected columns (e.g., `BG_1_<Subject>`, `BG_2_<Subject>`).
