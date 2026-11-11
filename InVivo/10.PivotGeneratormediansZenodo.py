"""
10.PivotGeneratormediansZenodo.py
Step 10 (InVivo, meal-based branch): median within-hour change and
reliability of each hour, expanded to the minute grid.

Created: 19 April 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Median of each hourly distribution of Boxplot<id>0-24total
       (MedRelChange, mmol/L), taken from the boxplot.
    2. Reliability of each hour from the number of days with a value in that
       hour, compared with this participant's 24 hourly counts:
           count <  50th percentile             -> 1 (low, red)
           50th <= count < 70th percentile      -> 2 (medium, yellow)
           count >= 70th percentile             -> 3 (high, green)
    3. Repeats the median and the flag of each hour over its 60 minutes.

Inputs
    globals.id, globals.fileToSave
    processed/<id>/Boxplot<id>0-24total.csv   (9.BoxplotZenodo.py)

Outputs
    processed/<id>/BGHourRelativeChange<id>0To24medians.csv        no header
    processed/<id>/BGHourRelativeChange<id>0To24medians_wCN.csv    Key, MedRelChange, Flag

Notes
    - The reliability thresholds are relative to the participant: by
      construction about half of the hours are low and about a third high.
    - The medians come from the matplotlib boxplot, which ignores empty
      values.
    - An hour with no data at all keeps a NaN median and flag 1.
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
id=globals.id;
# -----------------------------------------------------------#
# id=588;
# id="adolescent#006";
# id="child#010";
# id="adult#001";
path2= globals.fileToSave;
fileToRead="Boxplot"+str(id);
fileToSave="BGHourRelativeChange"+str(id);
# -----------------------------------------------------------#
dt = datetime.datetime(2010, 12, 1);
end = datetime.datetime(2010, 12, 1, 23, 59, 59);
step = datetime.timedelta(minutes=1);
secArray=[];
medians_a=[];
Flag_a=[];
# -----------------------------------------------------------#
# Open file and obtain medians
# -----------------------------------------------------------#
total=pd.read_csv(str(path2)+str(fileToRead)+str(0)+str("-")+str(24)+"total"+".csv");
_, bp = pd.DataFrame.boxplot(total, return_type='both');
medians = [median.get_ydata() for median in bp["medians"]];
# -----------------------------------------------------------#
# Obtain statistics of the number of lectures per hour
# -----------------------------------------------------------#
# Reliability: days with a value per hour, against this participant's P50 and P70.
values=pd.DataFrame();       
values=total.count(axis='rows');
low_b=np.percentile(values, 50);
upper_b=np.percentile(values, 70);
Flag=[]

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
open(str(path2)+str(fileToSave)+str("0To24")+"medians"+".csv", 'w').close();
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
for j in range(len(secArray)):
        file = open(str(path2)+str(fileToSave)+str("0To24")+"medians"+".csv", 'a');
        file.write(str(secArray[j])+","+str(medians_a[j])+","+str(Flag_a[j]));
        file.write('\n');
        file.close();
# -----------------------------------------------------------#
df = pd.read_csv(str(path2)+str(fileToSave)+str("0To24")+"medians"+".csv",  header=None);
df.rename(columns={0: 'Key',1:'MedRelChange',2:'Flag'}, inplace=True);
df.to_csv(str(path2)+str(fileToSave)+str("0To24")+"medians"+"_wCN"+".csv", index=False); # save to new csv
