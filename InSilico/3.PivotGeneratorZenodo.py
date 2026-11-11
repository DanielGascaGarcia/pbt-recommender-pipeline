"""
3.PivotGeneratorZenodo.py   (header of the original file reads 3.PivotGeneratorBG.py)
Step 3 (InSilico): write the minute grid of one day, used to join the
simulated glucose in 5.MergeBGComplete.

Created: 29 March 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Writes the 1,440 times of a day (00:00:00 ... 23:59:00), first without a
    header (PivotBG.csv) and then with the column name Key (PivotBG_wCN.csv).

Inputs
    globals.id, globals.fileToSave

Outputs (in processed/<id>/)
    PivotBG.csv, PivotBG_wCN.csv

Notes
    - Same script as InVivo/3.PivotGeneratorZenodo.py.
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
PathToSave = globals.fileToSave;
secArray=[];
# -----------------------------------------------------------#
open(str(PathToSave)+"PivotBG"+".csv", 'w').close();
while dt < end:
        secArray.append(dt.strftime('%H:%M:%S'));
        dt += step;
print(len(secArray));
# -----------------------------------------------------------#
for j in secArray:
        file = open(str(PathToSave)+"PivotBG"+".csv", 'a');
        file.write(str(j));
        print(str(j));
        file.write('\n');
        file.close();
# -----------------------------------------------------------#
df = pd.read_csv(str(PathToSave)+"PivotBG"+".csv",  header=None);
df.rename(columns={0: 'Key'}, inplace=True);
df.to_csv(str(PathToSave)+"PivotBG"+"_wCN"+".csv", index=False); # save to new csv
