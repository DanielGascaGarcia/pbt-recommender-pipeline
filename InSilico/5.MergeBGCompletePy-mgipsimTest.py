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

# Parameters
filesBG=[];


# --- Configurable global variable ---
id2=globals.id2;
id=globals.id;



path2=globals.fileToSave;
fileToSave="BGwNMLeftJoined"+str(id2)+".csv";


for file in os.listdir(path2):
    if file.startswith('BG'+str(id2) + '_'): 
        filesBG.append(file);
filesBG.sort(key=lambda x: int(re.search(r'_(\d+)', x).group(1)))
print(filesBG)


# reading two csv files
data1 = pd.read_csv(str(path2)+'PivotBG_wCN'+'.csv')
data2 = pd.read_csv(str(path2)+filesBG[0],usecols = ['Key','BGValue']);
data2.rename(columns = {'BGValue':'BGValue'+str(0)}, inplace = True);
data1['Key']=data1['Key'].str.strip();
data2['Key']=data2['Key'].str.strip();
output1 = pd.merge(data1,data2,suffixes=('',''),on='Key',how='left');
for j in range(len(filesBG)-1):
        data3 = pd.read_csv(str(path2)+filesBG[j+1],usecols = ['Key','BGValue']);
        data3.rename(columns = {'BGValue':'BGValue'+str(j+1)}, inplace = True);
        data3['Key']=data3['Key'].str.strip();
        output1 = pd.merge(output1,data3,suffixes=('',''),on='Key',how='left');
# Saving the result
output1.to_csv(str(path2)+str(fileToSave));
