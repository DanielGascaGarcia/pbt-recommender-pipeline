"""
13.InterpolationRChZenodo.py
Step 13 (InVivo): build the guide, a smooth curve of the median within-hour
change over the day, after setting aside atypical hours of low reliability.

Created: 10 May 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Takes one value per hour (MedRelChange and Flag at minute :59) and
       repeats the day 4 times (96 samples), so the spline has no edge
       effects at midnight.
    2. Hours of high reliability (Flag 3) are always kept. Among the other
       hours, values below the 25th or above the 75th percentile of those
       hours (over the 96 samples) are set aside.
    3. Fills the set-aside hours by linear interpolation between the kept
       ones, then fits a light smoothing spline (factor 0.1).
    4. Keeps the second of the 4 repeated days as BGRChInt.

Inputs
    globals.id, globals.fileToSave
    processed/<id>/ComparisonJoinedNoActivity<id>.csv   (12.MergeRChBasalNoActZenodo.py)

Output
    processed/<id>/SampleJoined<id>.csv
        the input columns + BGRChInt (guide, mmol/L, minute by minute)

Notes
    - The trimming keeps the central half of the non-green values; it is a
      range-based trim, not an outlier test. It is symmetric, so it does not
      push the guide up or down. Its effect is measured by
      S.TrimmingEffect.py.
    - Each hourly value sits at the end of its hour (minute :59).
    - The evaluation grid np.linspace(0, 5760, 5760) includes both ends, so
      its spacing is slightly above 1 minute (drift of up to ~1 min at the
      end of the window); negligible against the 60-min spacing of the
      nodes.
    - Sample['FRcH'].fillna('') is not assigned and has no effect.
    - G.CurveCheck.py and S.CurveAgreement.py replicate the trimming exactly
      to mark these hours.
"""

import pandas as pd
import os
from matplotlib import pyplot as plt
import numpy as np
import matplotlib
from datetime import datetime,timedelta
import datetime 
from scipy import interpolate
from scipy.interpolate import make_interp_spline
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import interp1d
matplotlib.rcParams.update({'font.size': 15})
# -----------------------------------------------------------#
# Parameters
# -----------------------------------------------------------#
import globals
id=globals.id;
# 540,544,552,567,584,596,559,563,570,575,588,591
# id=588;
# id="adolescent#006";
# id="child#010";
# id="adult#001";
# path2: processed/<id>/. Input: the joined table of step 12.
path2= globals.fileToSave;
fileToRead="ComparisonJoinedNoActivity"+str(id);
# fileToRead="ComparisonJoinedPeakNoActivity"+str(id);
fileToSave="SampleJoined"+str(id);
data = pd.read_csv(str(path2)+str(fileToRead)+".csv");

# Four days of minutes (1-4 Dec 2010; dates arbitrary): the hourly profile
# is repeated four times, so the spline has neighbours on both sides of
# midnight.
dt = datetime.datetime(2010, 12, 1);
end = datetime.datetime(2010, 12, 4, 23, 59, 59);
step = datetime.timedelta(minutes=1);


# -----------------------------------------------------------#
#                           Sample
# -----------------------------------------------------------#
# factor: smoothing factor of the spline (0.1 = light smoothing).
factor=0.1
Sample=pd.DataFrame();   
medTime=[];
medValue=[];
medIndex=[];
medFlag=[];

i=0;
j=0;
# One node per hour at minute :59, over 4 repeated days (96 samples).
# j = minute of the day (back to 0 every 1,440): the node of each hour is at
# j % 60 == 59. i = minute over the four days: the x of the node.
while dt < end:
       if j==1440:
          j=0;   
       if j%60==59:
              medTime.append(dt.strftime('%H:%M:%S'));
              medValue.append(data.loc[j, 'MedRelChange']);
              medFlag.append(data.loc[j, 'Flag']);
              medIndex.append(i);
       j=j+1;
       i=i+1;
       dt += step;

# -----------------------------------------------------------#
#                          Missings
# -----------------------------------------------------------#
# Sample: one row per node: time, median change of its hour (FRcH) and its
# flag. (The two fillna lines return a copy and change nothing.)
Sample['Key']=medTime;
Sample['FRcH']=medValue;
Sample['FRcH'].fillna('');
Sample['medFlag']=medFlag;
Sample['medFlag'].fillna('');
# -----------------------------------------------------------#
#                    Keep the least reliable
# -----------------------------------------------------------#

# Green hours (Flag 3) are never trimmed; only the other hours are checked.
# SampleL: the nodes of the hours that are not green (flag 1 or 2). If there
# are any, the trimming is applied to them; otherwise Sample_ = Sample.
SampleL = pd.DataFrame(Sample)
Sample_=SampleL
condition = SampleL['medFlag'] ==3;
SampleL = SampleL[~condition]
if len(SampleL)>0:

       # -----------------------------------------------------------#
       #                    Interquartile trimming of the non-green hours
       # -----------------------------------------------------------#

       # 25th, 50th and 75th percentiles of the median change over those nodes,
       # ignoring empty hours (the pandas version is computed but not used).
       percentiles = SampleL['FRcH'].quantile([0.25, 0.5, 0.75])
       percentiles_np = np.nanpercentile(SampleL['FRcH'], [25, 50, 75])
       print(percentiles_np[2])   # 75th percentile
       # -----------------------------------------------------------#
       #                    Filter values and eliminate duplicates
       # -----------------------------------------------------------#
       # Keep only the nodes within P25-P75 and drop repeated rows (each hour
       # appears once per repeated day).
       condition = SampleL['FRcH']<percentiles_np[0];
       SampleL = SampleL[~condition]
       condition = SampleL['FRcH']>percentiles_np[2];
       SampleL = SampleL[~condition]
       SampleL = SampleL.drop_duplicates();

       # # -----------------------------------------------------------#
       # #                     Merge interpolation
       # # -----------------------------------------------------------#
       Merge=pd.DataFrame(); 
       # Join the kept nodes back by time: _x = every node, _y = the kept ones.
       Sample['Key']=Sample['Key'].str.strip();
       SampleL['Key']=SampleL['Key'].str.strip();
       Sample_= pd.merge(Sample,SampleL,on='Key',how='left');


       # # # -----------------------------------------------------------#
       # # #                     Replace in original
       # # # -----------------------------------------------------------#

       # Define the condition for replacement
       # Every non-green node is emptied, then refilled with its own value only if
       # it was kept (within P25-P75). Trimmed nodes stay empty and are
       # interpolated below. Green nodes are never touched.
       condition_ = Sample_['medFlag_x']<3 
       # Replace values in column 'B' where the condition is True
       Sample_.loc[condition_, 'FRcH_x'] = np.nan


       # Define the condition for replacement
       condition__ = Sample_['medFlag_y'].notnull()
       # Replace values in column 'B' where the condition is True
       Sample_.loc[condition__, 'FRcH_x'] = Sample_.loc[condition__, 'FRcH_y']

       # Back to the column names FRcH and medFlag.
       Sample_.drop('medFlag_y', axis=1, inplace=True)
       Sample_.drop('FRcH_y', axis=1, inplace=True)
       Sample_.rename(columns={'medFlag_x': 'medFlag', 'FRcH_x': 'FRcH'}, inplace=True)

# -----------------------------------------------------------#
#                          Interpolation process
# -----------------------------------------------------------#
Interpolation=[];
Key=[];
RChToBeInt=[];
Interpolationdf=pd.DataFrame(); 
# Node values, with NaN at the trimmed hours.
RChToBeInt=Sample_['FRcH'].to_numpy();

# -----------------------------------------------------------#
#                     Linear Interpolation
# -----------------------------------------------------------#


# Find indices of missing values
missing_indices = np.isnan(RChToBeInt)

# Find indices of non-missing values
non_missing_indices = ~missing_indices

# Create an array of indices
indices = np.arange(len(RChToBeInt))

# Interpolate missing values
# Fill each empty node linearly between its neighbouring nodes.
RChToBeInt[missing_indices] = np.interp(indices[missing_indices], indices[non_missing_indices], RChToBeInt[non_missing_indices])

# -----------------------------------------------------------#
#                     Spline interpolation
# -----------------------------------------------------------#

# 5,760 points: four days, about one per minute.
xvals = np.linspace(0, 5760, 5760);

# Light smoothing spline over the 4 days; the second day is kept (rows 1439-2878).
X_Y_Spline =  UnivariateSpline(medIndex, RChToBeInt);
# X_Y_Spline =  UnivariateSpline(medIndex, medValue);
X_Y_Spline.set_smoothing_factor(factor)
Y_ = X_Y_Spline(xvals);
# Interpolation=np.interp(xvals,medIndex,RChToBeInt);
Interpolationdf['Key']=data['Key'];
Interpolationdf['BGRChInt']=Y_[1439:2879];
# # -----------------------------------------------------------#
# #                     Merge interpolation
# # -----------------------------------------------------------#
# Add BGRChInt to the table of step 12 and save it as SampleJoined<id>.csv:
# the reconstructed curve used to build the simulator input and by the
# agreement checks (G.CurveCheck, S.CurveAgreement).
Interpolationdf['Key']=Interpolationdf['Key'].str.strip();
output = pd.merge(data,Interpolationdf,on='Key',how='left');
# # -----------------------------------------------------------#
# #                     Saving
# # -----------------------------------------------------------#
output.to_csv(str(path2)+str(fileToSave)+".csv",index=False);
