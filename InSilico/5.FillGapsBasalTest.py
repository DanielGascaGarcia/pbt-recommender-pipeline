"""
5.FillGapsBasalTest.py   (header of the original file reads 5.FillGapsBasal.py)
Step 5 (InSilico): basal profile of the simulation in U/h, in the layout of
InVivo/5.FillGapsBasal.

Created: 22 March 2022
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Fills empty minutes forward and backward and writes ModeBasalValue =
    60 x (mode across columns), i.e. the simulated rate converted back from
    U/min to U/h.

Inputs
    globals.id, globals.id2, globals.fileToSave
    processed/<id>/BasalLeftJoined<id2>.csv   (step 0)

Output
    processed/<id>/BasalImputed<id2>.csv

Notes
    - There is a single basal column (the simulated profile), so the mode is
      the value itself. The tolerant mode of InVivo (smart_mode) is not
      needed here.
"""

import pandas as pd
import os

import globals
# --- Configurable global variable ---
id2=globals.id2;
id=globals.id;


# Same folder where 0.GeneratorExamplesPy-mgipsimForEGPtest.py writes
# BasalLeftJoined<id2>.csv.
# path2: processed/<id>/ of the participant.
path2=globals.fileToSave;
fileToRead="BasalLeftJoined"+str(id2)+".csv";
fileToSave="BasalImputed"+str(id2)+".csv";

# index_col=0: Key becomes the index, so the only column left is the rate.
data= pd.read_csv(str(path2)+fileToRead, index_col=0);
# Empty cells -> NaN, filled with the previous value (ffill) and, at the
# start of the day, with the next one (bfill).
df=data.replace('',float('NaN')).ffill().bfill();
# Mode across the columns of each minute (one column here, so the value
# itself; [0] = first mode), x 60: from U/min (step 0) back to U/h.
df["ModeBasalValue"]=60*df.mode(axis='columns',numeric_only=True)[0];
# Saved with the index, so Key is again the first column.
df.to_csv(str(path2)+str(fileToSave));
