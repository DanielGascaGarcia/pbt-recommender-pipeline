
#Code: 5.FillGapsBasal.py
#Description: Fill missing values and adding mode.
#Created 22nd March 2022
#Author: mbaxdg6

import pandas as pd
import pandas as pd
import numpy as np
import os

import globals
id=globals.id;


import pandas as pd
import numpy as np

# ---- Configuration ----
path2 = globals.fileToSave;
fileToRead = f'BasalLeftJoined{id}.csv'
fileToSave = f'BasalImputed{id}.csv'

# ---- Load & clean ----
data = pd.read_csv(path2 + fileToRead, index_col=0)
df = data.replace('', np.nan).ffill().bfill()

# ---- Smoothed mode function ----
def smart_mode(row, rounding_precision=3, min_freq_ratio=0.8):
    values = row.dropna().astype(float).values
    if len(values) == 0:
        return np.nan

    # Round values for tolerance
    rounded = np.round(values, rounding_precision)

    # Ignore zeros unless no other values exist
    nonzero = rounded[rounded > 0]
    if len(nonzero) == 0:
        return 0.0  # or np.nan if you prefer

    counts = pd.Series(nonzero).value_counts()
    max_count = counts.max()

    # Find all candidates close enough to the most frequent
    candidates = counts[counts >= min_freq_ratio * max_count]

    # Among them, choose the HIGHEST value
    return candidates.index.max()

# ---- Apply logic ----
df["ModeBasalValue"] = df.apply(smart_mode, axis=1)

# ---- Save result ----
df.to_csv(path2 + fileToSave)
print(f"✔ Saved final file to:\n{path2 + fileToSave}")
