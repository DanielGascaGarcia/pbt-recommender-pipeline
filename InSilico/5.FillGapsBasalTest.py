
#Code: 5.FillGapsBasal.py
#Description: Fill missing values and adding mode.
#Created 22nd March 2022
#Author: mbaxdg6

import pandas as pd
import os

import globals
# -----------------------------------------------------------#
# Configuration variables
# -----------------------------------------------------------#
id2=globals.id2;
id=globals.id;
path2=globals.fileToSave;
fileToRead="BasalLeftJoined"+str(id2)+".csv";
fileToSave="BasalImputed"+str(id2)+".csv";

data= pd.read_csv(str(path2)+fileToRead, index_col=0);
df=data.replace('',float('NaN')).ffill().bfill();
df["ModeBasalValue"]=60*df.mode(axis='columns',numeric_only=True)[0];
df.to_csv(str(path2)+str(fileToSave));

