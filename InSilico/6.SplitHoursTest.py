"""
6.SplitHoursTest.py
Step 6 (InSilico): split the joined simulated glucose into 24 hourly files.

Created: 19 April 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Same as InVivo/6.SplitHoursZenodo.py, on BGwNMLeftJoined<id2>.csv.

Inputs / Outputs
    processed/<id>/BGwNMLeftJoined<id2>.csv -> BGHour<id2><i>To<i+1>.csv

Notes
    - Key is read as row[1] because of the saved index column.
    - The steps of this chain are the InVivo steps applied to ONE simulated
      day, in mg/dL, with files named by the virtual patient (id2) inside
      processed/<id>/ of the participant.
"""

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


# path2: processed/<id>/. Input: the joined glucose of step 5; output prefix
# BGHour<id2>.
path2=globals.fileToSave;
fileToRead="BGwNMLeftJoined"+str(id2)+".csv";
fileToSave="BGHour"+str(id2);


# One file per hour i (0-23): BGHour<id2><i>To<i+1>.csv.
# Loop over all day round
for i in range(24):
    # csv.reader to go row by row; pandas only to read the header (data_top).
    # The file is read again for every hour.
    with open(str(path2)+str(fileToRead)) as csv_file:
                reader = csv.reader(csv_file);
                next(reader); #skip header
                data = pd.read_csv(str(path2)+str(fileToRead)); 
                data_top = data.columns;
                print(data_top); 
                # Window of hour i: i:00:00 to i:59:59 (the date is arbitrary).
                dt1 = datetime.datetime(2010, 12, 1,i,0,0);
                dt2 = datetime.datetime(2010, 12, 1,i,59,59);
                with open(str(path2)+str(fileToSave)+str(i)+str("To")+str(i+1)+".csv", 'w', newline='') as fout:
                            csv_output = csv.writer(fout);
                            # Header first, then every row whose time falls in the window.
                            csv_output.writerow(data_top);  #header
                            for row in reader:
                                # row[1] is Key (row[0] is the saved index). Times are compared as
                                # HH:MM:SS text, which sorts in time order.
                                split=datetime.datetime(2010, 12, 1,int(row[1][0:2]),int(row[1][3:5]),int(row[1][6:8])); 
                                if dt1.strftime('%H:%M:%S')<=split.strftime('%H:%M:%S')<=dt2.strftime('%H:%M:%S'):
                                    # print (row[1]);
                                    csv_output.writerow(row);
