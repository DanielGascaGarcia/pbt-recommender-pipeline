"""
9.BoxplotZenodo.py
Step 9 (InVivo, meal-based branch): gather the within-hour changes of all
days into one table (one column per hour) and draw their boxplot.

Created: 10 May 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Reads the 24 lastValues files of 8.RelativeChange and writes them as the
    columns [0-1] ... [23-24] of one table, one row per analysis day. Draws
    the boxplot of the 24 hourly distributions (hours in reverse order, so
    00-01 is at the top).

Inputs
    globals.id, globals.fileToSave, globals.MGDL_PER_MMOL
    processed/<id>/BGHourRelativeChange<id><i>To<i+1>(lastValues).csv   (8.RelativeChangeZenodo.py)

Output
    processed/<id>/Boxplot<id>0-24total.csv   24 columns, one row per day

Notes
    - The number of rows is the column count of the first relative-change
      file minus 1 (Key), i.e. the number of analysis days.
    - Within each column the values are not aligned with day numbers (see
      the Notes of 8.RelativeChange); only the hourly distribution is used.
    - The shaded band of the figure is drawn at +/- 2 x MGDL_PER_MMOL
      (+/- 36) while the values are in mmol/L, so it covers the whole axis.
      This affects the figure only, not the table.
    - plt.show() opens the figure; the orchestrator sets the Agg backend so
      it does not block.
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
id=globals.id;

path2= globals.fileToSave;
fileToRead="BGHourRelativeChange"+str(id);
fileToSave="Boxplot"+str(id);

# One row per analysis day: the relative-change file has Key plus one column
# per day, so the number of days is the column count minus 1.
# -----------------------------------------------------------#
# Obtain the last values
# -----------------------------------------------------------#
# One row per analysis day: column count of the relative-change file minus Key.
total = pd.DataFrame(index=range(len(pd.read_csv(str(path2)+str(fileToRead)+str(0)+str("To")+str(1)+".csv").columns)-1));
for i in reversed(range(24)):
    data = pd.read_csv(str(path2)+str(fileToRead)+str(i)+str("To")+str(i+1)+"lastValues"+".csv");
    data.rename(columns = {'Last_values':str(i)+str("-")+str(i+1)}, inplace = True);
    total[str(i)+"-"+str(i+1)]=1*data[str(i)+str("-")+str(i+1)];
# -----------------------------------------------------------#
# Saving in the correct order
# -----------------------------------------------------------#
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
# -----------------------------------------------------------#
# Figure (not saved to file)
# -----------------------------------------------------------#
plt.grid();
pd.DataFrame.boxplot(total, vert = False);
# -----------------------------------------------------------#
# Display the plot
# -----------------------------------------------------------#
plt.xlabel("Blood Glucose Relative Change \n (mg/dL) (mmol/L)");
plt.ylabel("Hours");
plt.axvspan(-2*globals.MGDL_PER_MMOL, 2*globals.MGDL_PER_MMOL, color="blue", alpha=0.2)
plt.title("Blood Glucose Relative Change Behaviour, ID: "+str(id));
plt.show();
