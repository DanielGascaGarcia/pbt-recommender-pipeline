#Description: Merge of values.
#Created 11th April 2023
#Author: mbaxdg6


import datetime 
import pandas as pd
import os
from datetime import datetime,timedelta
import datetime 
from matplotlib import pyplot as plt
import numpy as np
import re
import globals
# Parameters


filesBG=[];
# -----------------------------------------------------------#
# Configuration
# -----------------------------------------------------------#
# --- Configurable global variable ---
id=globals.id;

# --- Folder paths ---
filetoread = globals.fileToSave
PathToSave= globals.fileToSave
fileToSave="BGwNMLeftJoined"+str(id)+".csv";

# -----------------------------------------------------------#
#                  Files of BG
# -----------------------------------------------------------#

# Find and collect all matching BG files
for file in os.listdir(filetoread):
    if file.startswith(f'_UoMGlucose{id}_') and file.endswith('.csv'):
        filesBG.append(file)

# Sort files by the date part in filename (YYYYMMDD)
filesBG.sort(key=lambda x: int(re.search(r'_(\d{8})', x).group(1)))


if len(filesBG)>=2:
    # reading two csv files
    data1 = pd.read_csv(str(filetoread)+'PivotBG_wCN'+'.csv')
    data2 = pd.read_csv(str(filetoread)+filesBG[0],usecols = ['Key','BGValue']);
    data2.rename(columns = {'BGValue':'BGValue'+str(0)}, inplace = True);
    data1['Key']=data1['Key'].str.strip();
    data2['Key']=data2['Key'].str.strip();
    output1 = pd.merge(data1,data2,suffixes=('',''),on='Key',how='left');
    for j in range(len(filesBG)-1):
            data3 = pd.read_csv(str(filetoread)+filesBG[j+1],usecols = ['Key','BGValue']);
            data3.rename(columns = {'BGValue':'BGValue'+str(j+1)}, inplace = True);
            data3['Key']=data3['Key'].str.strip();
            output1 = pd.merge(output1,data3,suffixes=('',''),on='Key',how='left');
# Saving the result
output1.to_csv(str(PathToSave)+str(fileToSave));
