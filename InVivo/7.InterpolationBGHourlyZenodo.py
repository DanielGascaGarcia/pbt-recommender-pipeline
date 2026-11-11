"""
7.InterpolationBGHourlyZenodo.py
Step 7 (InVivo, meal-based branch): fill short gaps inside each hourly file.

Created: 19 April 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    In each of the 24 hourly files, interpolates every day column linearly
    over gaps of up to 5 minutes, in both directions. With CGM readings every
    5 minutes this fills the minutes between readings; longer gaps (sensor
    dropout, removed meal windows) stay empty.

Inputs
    globals.id, globals.fileToSave
    processed/<id>/BGHour<id><i>To<i+1>.csv   (6.SplitHoursZenodo.py)

Outputs
    processed/<id>/BGHourInterpolated<id><i>To<i+1>.csv

Notes
    - Interpolation stays inside the hour: it does not cross hourly files.
    - The commented lines (hourly mean, median, SD) are not used.
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
import globals
id=globals.id;

# id=588;
# id="adolescent#006";
# id="child#010";
# id="adult#001";
path2= globals.fileToSave;
fileToRead="BGHour"+str(id);
fileToSave="BGHourInterpolated"+str(id);
warnings.simplefilter(action='ignore', category=FutureWarning)

for i in range(24):
    data = pd.read_csv(str(path2)+str(fileToRead)+str(i)+str("To")+str(i+1)+".csv"); 
    dI=data.interpolate(limit=5, limit_direction='both');
    # dI["MeanBGValue"]=dI.mean(axis='columns',numeric_only=True);
    # dI["MedianBGValue"]=dI.median(axis='columns',numeric_only=True);
    # dI["STDBGValue"]=dI.std(axis='columns',numeric_only=True);
    # print(dI.columns);
    dI.to_csv(str(path2)+str(fileToSave)+str(i)+str("To")+str(i+1)+".csv",index=False);
