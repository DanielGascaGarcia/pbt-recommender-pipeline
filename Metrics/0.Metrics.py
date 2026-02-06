#Code: 0.,Metrics.py
#Description: Metrics of Basal Insulin recommendation.
#Created 11th Oct 2025
#Author: mbaxdg6

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import globals

# ----------------------------------------------------------
# 0. Global style configuration — larger fonts
# ----------------------------------------------------------
plt.rcParams.update({
    'font.size': 14,            # Base font size
    'axes.titlesize': 18,       # Title font
    'axes.labelsize': 16,       # Axis labels
    'xtick.labelsize': 13,      # X tick labels
    'ytick.labelsize': 13,      # Y tick labels
    'legend.fontsize': 13,      # Legend text
    'figure.titlesize': 18,     # Overall figure title
    'figure.autolayout': True   # Better spacing automatically
})

# ----------------------------------------------------------
# Load the Excel file
# ----------------------------------------------------------
folder_path = globals.folder_path
file_name   = globals.file_name   # Change this to Day1.xlsx, Day2.xlsx, etc.
file_path   = os.path.join(folder_path, file_name)


day_number = ''.join(filter(str.isdigit, file_name))  
day_label  = f"Day {day_number}" if day_number else "Unknown Day"


df = pd.read_excel(file_path)

# ----------------------------------------------------------
# Define helper functions
# ----------------------------------------------------------
def mmol_to_mgdl(value):
    """Convert mmol/L to mg/dL."""
    return value * 18.0182

# ----------------------------------------------------------
# Extract subjects and compute metrics
# ----------------------------------------------------------
subjects = sorted(set(c.split("_")[-1] for c in df.columns))
results = []

eps = 1e-12  # numerical safety

for subj in subjects:
    bg1 = df[f'BG_1_{subj}'].dropna()
    bg2 = df[f'BG_2_{subj}'].dropna()


    std1 = bg1.std()
    std2 = bg2.std()
    reduction_std = ((std1 - std2) / std1) * 100 if std1 != 0 else np.nan


    tamae1 = np.mean(np.abs(bg1 - 6))
    tamae2 = np.mean(np.abs(bg2 - 6))
    delta_tamae = tamae1 - tamae2


    std_ratio  = (std1 + eps) / (std2 + eps)
    tamae_ratio = (tamae1 + eps) / (tamae2 + eps)
    composite_index = np.sqrt(std_ratio * tamae_ratio)


    results.append({
        'Subject': subj,
        'STD_1_mmolL': std1,
        'STD_2_mmolL': std2,
        'STD_1_mgdl': mmol_to_mgdl(std1),
        'STD_2_mgdl': mmol_to_mgdl(std2),
        'STD_Reduction_%': reduction_std,
        'ΔtaMAE_mmolL': delta_tamae,
        'ΔtaMAE_mgdl': mmol_to_mgdl(delta_tamae),
        'Composite_Index': composite_index
    })


df_results = pd.DataFrame(results)
print(f"\n=== {day_label} Results Summary ===")
print(df_results.round(3))

# ----------------------------------------------------------
#                          Plots
# ----------------------------------------------------------
plt.figure(figsize=(7,7))

plt.scatter(df_results['STD_1_mmolL'],
            df_results['STD_2_mmolL'],
            color='royalblue',
            s=80)  # Bigger points

max_val = max(df_results['STD_1_mmolL'].max(),
              df_results['STD_2_mmolL'].max())

plt.plot([0, max_val], [0, max_val], 'r--', label='Identity line (no change)')
plt.xlabel("STD Before (mmol/L)")
plt.ylabel("STD After (mmol/L)")
plt.title(f"Glucose Variability Before vs After Basal Adjustment — {day_label}")
plt.legend()
plt.grid(alpha=0.3)
ax2 = plt.gca().twinx()
ax2.set_ylim(plt.ylim()[0] * 18.0182, plt.ylim()[1] * 18.0182)
ax2.set_ylabel("Blood Glucose (mg/dL)")
plt.tight_layout()
plt.show()


plt.figure(figsize=(10,6))
plt.bar(df_results['Subject'], df_results['ΔtaMAE_mmolL'], color='cornflowerblue')
plt.axhline(0, color='gray', linestyle='--', linewidth=1)
plt.xticks(rotation=45, ha='right')
plt.ylabel("ΔtaMAE (mmol/L)")
plt.title(f"Improvement in Mean Deviation from Target (6 mmol/L) — {day_label}")
plt.grid(axis='y', alpha=0.3)
ax2 = plt.gca().twinx()
ax2.set_ylim(plt.ylim()[0] * 18.0182, plt.ylim()[1] * 18.0182)
ax2.set_ylabel("ΔtaMAE (mg/dL)")
plt.tight_layout()
plt.show()


plt.figure(figsize=(10,6))
plt.bar(df_results['Subject'],
        df_results['Composite_Index'],
        color='mediumorchid')

plt.axhline(1, color='gray', linestyle='--', linewidth=1, label='No change (I=1)')
plt.xticks(rotation=45, ha='right')
plt.ylabel("Composite Stability Index (I)")
plt.title(f"Composite Stability Index Across Subjects — {day_label}")
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()
