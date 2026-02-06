#Description: interpolate values.
#Created 19th April 2023
#Author: mbaxdg6

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



# --- Configurable global variable ---
id=globals.id;
print(id)
id2=globals.id2;
print(id2)
path2=globals.fileToSave
fileToRead="BGHour"+str(id2);
fileToSave="BGHourInterpolated"+str(id2);
warnings.simplefilter(action='ignore', category=FutureWarning)

for i in range(24):
    data = pd.read_csv(str(path2)+str(fileToRead)+str(i)+str("To")+str(i+1)+".csv"); 
    dI=data.interpolate(limit=5, limit_direction='both');
    # dI["MeanBGValue"]=dI.mean(axis='columns',numeric_only=True);
    # dI["MedianBGValue"]=dI.median(axis='columns',numeric_only=True);
    # dI["STDBGValue"]=dI.std(axis='columns',numeric_only=True);
    # print(dI.columns);
    dI.to_csv(str(path2)+str(fileToSave)+str(i)+str("To")+str(i+1)+".csv",index=False);