#Code: 3.PivotGeneratorZenodo.py
#Description: Creating pivot table for merge.
#Created 29th March 2023
#Author: mbaxdg6

import datetime 
import pandas as pd

import globals
# -----------------------------------------------------------#
# Configuration variables
# -----------------------------------------------------------#

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