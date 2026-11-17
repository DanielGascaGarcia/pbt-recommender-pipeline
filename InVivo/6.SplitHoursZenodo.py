"""
6.SplitHoursZenodo.py
Step 6 (InVivo, meal-based branch): split the joined glucose file into 24
hourly files.

Created: 19 April 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    For each hour i (0 to 23), copies the rows of BGwNMLeftJoined whose Key
    falls between i:00:00 and i:59:59 into BGHour<id><i>To<i+1>.csv, with
    the same columns.

Inputs
    globals.id, globals.fileToSave
    processed/<id>/BGwNMLeftJoined<id>.csv   (5.MergeBGCleanZenodo.py)

Outputs
    processed/<id>/BGHour<id>0To1.csv ... BGHour<id>23To24.csv   60 rows each

Notes
    - Key is read as the SECOND field of each row (row[1]) because the
      joined file carries the saved index as its first column.
    - The input is read twice per hour (csv reader for the rows, pandas for
      the header); slow but harmless.
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
id=globals.id;
# id=588;
# id="adolescent#006";
# id="child#010";
# id="adult#001";
# path2: processed/<id>/. Input: the joined glucose of step 5; output prefix
# BGHour<id>. (The commented ids above are from earlier datasets.)
path2= globals.fileToSave;
fileToRead="BGwNMLeftJoined"+str(id)+".csv";
fileToSave="BGHour"+str(id);


# Loop over all day round
# row[1] is Key: the first column of the joined file is the saved index.
# One file per hour i (0-23): BGHour<id><i>To<i+1>.csv.
for i in range(24):
    # csv.reader to go row by row; pandas only to read the header (data_top).
    # The file is read again for every hour.
    with open(str(path2)+str(fileToRead)) as csv_file:
                reader = csv.reader(csv_file);
                next(reader); #skip header
                data = pd.read_csv(str(path2)+str(fileToRead)); 
                data_top = data.columns;
                print(data_top); 
                # Window of hour i: i:00:00 to i:59:59 (date arbitrary).
                dt1 = datetime.datetime(2010, 12, 1,i,0,0);
                dt2 = datetime.datetime(2010, 12, 1,i,59,59);
                with open(str(path2)+str(fileToSave)+str(i)+str("To")+str(i+1)+".csv", 'w', newline='') as fout:
                            csv_output = csv.writer(fout);
                            # Header first, then every row whose time falls in the window.
                            csv_output.writerow(data_top);  #header
                            for row in reader:
                                # Times compared as HH:MM:SS text, which sorts in time order.
                                split=datetime.datetime(2010, 12, 1,int(row[1][0:2]),int(row[1][3:5]),int(row[1][6:8])); 
                                if dt1.strftime('%H:%M:%S')<=split.strftime('%H:%M:%S')<=dt2.strftime('%H:%M:%S'):
                                    # print (row[1]);
                                    csv_output.writerow(row);
