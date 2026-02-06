#Code: 4.MergeBasalZenodo.py
#Description: Create examples from  py-mgipsim simulator.
#Created 24th October 2022
#Author: mbaxdg6

import os
import pandas as pd
import globals
# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#


import os
import pandas as pd
import re
from datetime import datetime

# --- Configurable global variable ---
id = globals.id

# Construct paths
base_path = globals.fileToSave;
pivot_file = os.path.join(base_path, 'Pivot_wCN.csv')
file_pattern = f"UoMBasal{id}_"
output_file = f"BasalLeftJoined{id}.csv"

# 1) Load the pivot dataframe
pivot_df = pd.read_csv(pivot_file)
pivot_df['Key'] = pivot_df['Key'].astype(str).str.strip()

# 2) Find and sort basal files by date
all_files = os.listdir(base_path)
basal_files = [
    f for f in all_files 
    if f.startswith(file_pattern) and f.endswith('.csv')
]

# Extract date from filename and sort
def extract_date(fname):
    match = re.search(rf'{file_pattern}(\d{{8}})', fname)
    if match:
        return datetime.strptime(match.group(1), "%Y%m%d")
    return datetime.max  # Push unparseable names to the end

# Sort by date and select first 45
basal_files = sorted(basal_files, key=extract_date)[:45]
print("Selected basal files:", basal_files)

if not basal_files:
    print("No basal files matching pattern found.")
else:
    # 3) Start from a copy of the pivot
    merged_df = pivot_df.copy()

    for i, fname in enumerate(basal_files):
        full_path = os.path.join(base_path, fname)
        df = pd.read_csv(full_path)

        # 3a) Confirm that the file has at least “Key” and “basal_dose”
        missing_cols = [c for c in ['Key', 'basal_dose'] if c not in df.columns]
        if missing_cols:
            print(f"  → Skipping {fname}: missing columns {missing_cols}")
            continue

        # 3b) Clean up whitespace
        df['Key'] = df['Key'].astype(str).str.strip()

        # 3c) Rename basal_dose → basal_dose_{i}
        new_dose_col = f"basal_dose_{i}"
        df = df.rename(columns={'basal_dose': new_dose_col})

        # 3d) Keep only “Key” + new dose column
        df_sub = df[['Key', new_dose_col]].copy()

        # 3e) Merge
        merged_df = pd.merge(
            merged_df,
            df_sub,
            on='Key',
            how='left'
        )

    # 4) Drop duplicate keys
    merged_df = merged_df.drop_duplicates(subset=['Key'], keep='first')

    # 5) Write out final CSV
    out_path = os.path.join(base_path, output_file)
    merged_df.to_csv(out_path, index=False)
    print(f"→ Merged basal‐dose file written to:\n   {out_path}")
