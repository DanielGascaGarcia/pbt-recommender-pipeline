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
id = globals.id;

dt = datetime.datetime(2010, 12, 1);
end = datetime.datetime(2010, 12, 1, 23, 59, 59);
step = datetime.timedelta(minutes=1);
path2=globals.fileToSave;
secArray=[];

open(str(path2)+"Pivot"+".csv", 'w').close();

while dt < end:
        secArray.append(dt.strftime('%H:%M:%S'));
        dt += step;

print(len(secArray));

for j in secArray:
        file = open(str(path2)+"Pivot"+".csv", 'a');
        file.write(str(j));
        print(str(j));
        file.write('\n');
        file.close();


df = pd.read_csv(str(path2)+"Pivot"+".csv",  header=None);
df.rename(columns={0: 'Key'}, inplace=True);
df.to_csv(str(path2)+"Pivot"+"_wCN"+".csv", index=False); # save to new csv
