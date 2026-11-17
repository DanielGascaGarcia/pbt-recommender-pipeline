"""
9.BoxplotTest.py
Step 9 (InSilico): gather the within-hour changes into one table (one column
per hour) and draw their boxplot.

Created: 10 May 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Same as InVivo/9.BoxplotZenodo.py. With one simulated day, the table has
    one row.

Inputs / Output
    BGHourRelativeChange<id2>... -> Boxplot<id2>0-24total.csv

Notes
    - The number of rows is the column count of the relative-change file
      minus Key (-1; it was -2 before, which would drop the last day with
      2 or more days).
    - Here the values are in mg/dL, so the shaded band at +/- 2 x
      MGDL_PER_MMOL (+/- 2 mmol/L) is at the right scale.
"""

import datetime 
import pandas as pd
import os
from datetime import datetime,timedelta
import datetime 
from matplotlib import pyplot as plt
import numpy as np
import csv
import seaborn as sns
import matplotlib
matplotlib.rcParams.update({'font.size': 18})
import globals
# --- Configurable global variable ---
id=globals.id;
print(id)
id2=globals.id2;
print(id2)
# path2: processed/<id>/.
path2=globals.fileToSave;
fileToRead="BGHourRelativeChange"+str(id2);
fileToSave="Boxplot"+str(id2);

# One row per day: the relative-change file has Key plus one column per day,
# so the number of days is the column count minus 1.
# -----------------------------------------------------------#
# Obtain the last values
# -----------------------------------------------------------#
total = pd.DataFrame(index=range(len(pd.read_csv(str(path2)+str(fileToRead)+str(0)+str("To")+str(1)+".csv").columns)-1));
# total: one row per day, one column per hour 'i-i+1' with the net change of
# that hour (built from the last hour backwards; used for the boxplot).
for i in reversed(range(24)):
    data = pd.read_csv(str(path2)+str(fileToRead)+str(i)+str("To")+str(i+1)+"lastValues"+".csv");
    data.rename(columns = {'Last_values':str(i)+str("-")+str(i+1)}, inplace = True);
    total[str(i)+"-"+str(i+1)]=1*data[str(i)+str("-")+str(i+1)];
# -----------------------------------------------------------#
# Saving in the correct order
# -----------------------------------------------------------#
# total1: the same values, columns '[i-i+1]' in order 0-24. This is the
# table saved and read by step 10.
total1 = pd.DataFrame(index=range(len(pd.read_csv(str(path2)+str(fileToRead)+str(0)+str("To")+str(1)+".csv").columns)-1));
for i in range(24):
    data = pd.read_csv(str(path2)+str(fileToRead)+str(i)+str("To")+str(i+1)+"lastValues"+".csv");
    data.rename(columns = {'Last_values':"["+str(i)+str("-")+str(i+1)+"]"}, inplace = True);
    print(str(i)+str("-")+str(i+1));
    total1["["+str(i)+"-"+str(i+1)+"]"]=data["["+str(i)+str("-")+str(i+1)+"]"];
total1.to_csv(str(path2)+str(fileToSave)+str(0)+str("-")+str(24)+"total"+".csv",index=False);

# -----------------------------------------------------------#
# Plot the dataframe
# -----------------------------------------------------------#
# Horizontal boxplot of the 24 hours; the blue band marks +/- 2 mmol/L
# (written in mg/dL). Shown, not saved (the orchestrator sets Agg).
plt.grid();
pd.DataFrame.boxplot(total, vert = False);
# -----------------------------------------------------------#
# Display the plot
# -----------------------------------------------------------#
plt.xlabel("Blood Glucose Relative Change \n (mg/dL) (mmol/L)");
plt.ylabel("Hours");
plt.axvspan(-2*globals.MGDL_PER_MMOL, 2*globals.MGDL_PER_MMOL, color="blue", alpha=0.2)
plt.title("Blood Glucose Relative Change Behaviour, ID: "+str(id2));
plt.show();
