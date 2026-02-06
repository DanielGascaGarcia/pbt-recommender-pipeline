
#Code: 5.FillGapsBasalZenodo.py
#Description: Fill missing values and adding mode.
#Created 22nd March 2022
#Author: mbaxdg6

import pandas as pd
import pandas as pd
import numpy as np
import os
import globals

# -----------------------------------------------------------#
# Configuration variables
# -----------------------------------------------------------#
id=globals.id;
path2 = globals.fileToSave;
fileToRead = f'BasalLeftJoined{id}.csv'
fileToSave = f'BasalImputed{id}.csv'

data = pd.read_csv(path2 + fileToRead, index_col=0)
df = data.replace('', np.nan).ffill().bfill()


def smart_mode(row, rounding_precision=3, min_freq_ratio=0.8):
    values = row.dropna().astype(float).values
    if len(values) == 0:
        return np.nan


    rounded = np.round(values, rounding_precision)
    nonzero = rounded[rounded > 0]
    if len(nonzero) == 0:
        return 0.0  

    counts = pd.Series(nonzero).value_counts()
    max_count = counts.max()
    candidates = counts[counts >= min_freq_ratio * max_count]
    return candidates.index.max()


df["ModeBasalValue"] = df.apply(smart_mode, axis=1)
df.to_csv(path2 + fileToSave)
print(f"✔ Saved final file to:\n{path2 + fileToSave}")
