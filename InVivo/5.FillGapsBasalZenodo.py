"""
5.FillGapsBasalZenodo.py   (header of the original file reads 5.FillGapsBasal.py)
Step 5 (InVivo, basal branch): fill the minutes between programmed basal
rates and summarise the days into one representative profile.

Created: 22 March 2022
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Fills every day column forward in time (each rate holds until the
       next one) and backward at the start of the day.
    2. For every minute, takes the most frequent rate across days
       (ModeBasalValue), with tolerance:
         - rates rounded to 3 decimals;
         - zeros ignored unless every day is 0;
         - every rate whose count is at least 80% of the top count is a
           candidate, and the highest candidate is chosen.

Inputs
    globals.id, globals.fileToSave
    processed/<id>/BasalLeftJoined<id>.csv   (4.MergeBasalZenodo.py)

Output
    processed/<id>/BasalImputed<id>.csv   day columns filled + ModeBasalValue

Notes
    - Choosing the highest of the near-ties keeps the profile on the side of
      the larger programmed rate when two rates are almost equally common.
    - A minute with no rate in any day gives NaN (cannot happen after the
      forward and backward fill unless a whole column is empty).
"""

# Imports repeated from the original; harmless.
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
# index_col=0: Key becomes the index; the day columns remain.
data = pd.read_csv(path2 + fileToRead, index_col=0)
# Each programmed rate holds until the next one (ffill); bfill covers the first minutes.
df = data.replace('', np.nan).ffill().bfill()

# ---- Smoothed mode function ----
def smart_mode(row, rounding_precision=3, min_freq_ratio=0.8):
    # Rates of this minute across the days, as numbers, without empty values.
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
# One value per minute: ModeBasalValue, the representative programmed rate
# (U/h).
df["ModeBasalValue"] = df.apply(smart_mode, axis=1)

# ---- Save result ----
# Saved with the index, so Key is again the first column.
df.to_csv(path2 + fileToSave)
print(f"✔ Saved final file to:\n{path2 + fileToSave}")
