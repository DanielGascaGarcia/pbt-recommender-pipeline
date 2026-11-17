"""
10.PivotGeneratormediansTest.py
Step 10 (InSilico): median within-hour change and reliability of each hour,
expanded to the minute grid.

Created: 19 April 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Same as InVivo/10.PivotGeneratormediansZenodo.py.

Inputs / Outputs
    Boxplot<id2>0-24total.csv -> BGHourRelativeChange<id2>0To24medians(_wCN).csv

Notes
    - With a single simulated day, every hour has exactly one value, so all
      24 counts are equal and every hour gets reliability 3 (high). As a
      result, step 13 sets nothing aside in silico (see its Notes).
"""

import warnings
import datetime 
import pandas as pd
import os
from datetime import datetime,timedelta
import datetime 
from matplotlib import pyplot as plt
import numpy as np
import csv
import seaborn as sns
warnings.simplefilter(action='ignore', category=FutureWarning)

import globals
# --- Configurable global variable ---
id=globals.id;
print(id)
id2=globals.id2;
print(id2)
# path2: processed/<id>/.
path2=globals.fileToSave;
fileToRead="Boxplot"+str(id2);
fileToSave="BGHourRelativeChange"+str(id2);
# -----------------------------------------------------------#
# Minute grid of one day (date arbitrary).
dt = datetime.datetime(2010, 12, 1);
end = datetime.datetime(2010, 12, 1, 23, 59, 59);
step = datetime.timedelta(minutes=1);
secArray=[];
medians_a=[];
Flag_a=[];
# -----------------------------------------------------------#
# Open file and obtain medians
# -----------------------------------------------------------#
# Hourly medians, taken from the boxplot of the table of step 9 (the median
# line of each box). medians[i] holds the y values of that line (two equal
# points); [0] is used below.
total=pd.read_csv(str(path2)+str(fileToRead)+str(0)+str("-")+str(24)+"total"+".csv");
_, bp = pd.DataFrame.boxplot(total, return_type='both');
medians = [median.get_ydata() for median in bp["medians"]];
# -----------------------------------------------------------#
# Obtain statistics of the number of lectures per hour
# -----------------------------------------------------------#
# Reliability of each hour from how many days have a value in it:
#   values  = count per hour
#   low_b   = 50th percentile of the 24 counts
#   upper_b = 70th percentile of the 24 counts
values=pd.DataFrame();       
values=total.count(axis='rows');
low_b=np.percentile(values, 50);
upper_b=np.percentile(values, 70);
Flag=[]

# Flag 1 (low, red): fewer days than low_b; 3 (high, green): upper_b or
# more; 2 (medium, yellow): in between. In silico every count is 1, so every
# hour gets 3.
for i in range(len(values)):
 if values[i]<low_b:
    Flag.append(1);
 elif values[i]>=upper_b:
    Flag.append(3);
 else:
    Flag.append(2);
print(Flag);

# -----------------------------------------------------------#
# Obtain the pivot and variables needed to graph
# -----------------------------------------------------------#
# Create (or empty) the output file.
open(str(path2)+str(fileToSave)+str("0To24")+"medians"+".csv", 'w').close();
# For each minute: its time, the median of its hour and the flag of its hour.
# j counts the minutes; every 60 the hour index i moves on.
i=0;
j=1;
while dt < end:
        secArray.append(dt.strftime('%H:%M:%S'));
        medians_a.append(medians[i][0]);
        Flag_a.append(Flag[i]);
        # print(i);
        dt += step;
        if j%60==0:
              i=i+1;
        j=j+1;
# -----------------------------------------------------------#
# One line per minute: Key, median, flag (no header).
for j in range(len(secArray)):
        file = open(str(path2)+str(fileToSave)+str("0To24")+"medians"+".csv", 'a');
        file.write(str(secArray[j])+","+str(medians_a[j])+","+str(Flag_a[j]));
        file.write('\n');
        file.close();
# -----------------------------------------------------------#
# Read back, name the columns Key, MedRelChange, Flag and save as _wCN (with
# column names).
df = pd.read_csv(str(path2)+str(fileToSave)+str("0To24")+"medians"+".csv",  header=None);
df.rename(columns={0: 'Key',1:'MedRelChange',2:'Flag'}, inplace=True);
df.to_csv(str(path2)+str(fileToSave)+str("0To24")+"medians"+"_wCN"+".csv", index=False); # save to new csv
