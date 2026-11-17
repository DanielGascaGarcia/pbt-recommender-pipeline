"""
3.PivotGeneratorBasalZenodo.py   (header of the original file reads 3.PivotGeneratorBasal.py)
Step 3 (InVivo, basal): write the minute grid of one day, used to join the
daily basal files in 4.MergeBasal.

Created: 22 March 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Writes the 1,440 times of a day (00:00:00 ... 23:59:00), first without a
    header (Pivot.csv) and then with the column name Key (Pivot_wCN.csv).

Inputs
    globals.id, globals.fileToSave

Outputs (in processed/<id>/)
    Pivot.csv, Pivot_wCN.csv

Notes
    - Same grid as 3.PivotGeneratorZenodo.py, written to a different file
      name for the basal branch.
"""

import datetime 
import pandas as pd

import globals
# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#


# --- Configurable global variable ---
# id: participant; the grid is written to its processed/<id>/.
id = globals.id;

# One day at 1-minute steps. The date (1 Dec 2010) is arbitrary: only the
# time of day is used.
dt = datetime.datetime(2010, 12, 1);
end = datetime.datetime(2010, 12, 1, 23, 59, 59);
step = datetime.timedelta(minutes=1);
path2=globals.fileToSave;
secArray=[];

# Create (or empty) Pivot.csv before appending to it.
open(str(path2)+"Pivot"+".csv", 'w').close();

# secArray: the 1,440 times 00:00:00 ... 23:59:00, as text.
while dt < end:
        secArray.append(dt.strftime('%H:%M:%S'));
        dt += step;

# Prints 1440, as a check.
print(len(secArray));

# One time per line (no header); the file is opened in append mode for each
# line.
for j in secArray:
        file = open(str(path2)+"Pivot"+".csv", 'a');
        file.write(str(j));
        print(str(j));
        file.write('\n');
        file.close();


# Read back without header, name the column Key and save as Pivot_wCN.csv
# (wCN = with column name): the grid 4.MergeBasalZenodo.py joins the basal onto.
df = pd.read_csv(str(path2)+"Pivot"+".csv",  header=None);
df.rename(columns={0: 'Key'}, inplace=True);
df.to_csv(str(path2)+"Pivot"+"_wCN"+".csv", index=False); # save to new csv
