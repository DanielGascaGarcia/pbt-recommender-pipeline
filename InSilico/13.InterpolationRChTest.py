"""
13.InterpolationRChTest.py
Step 13 (InSilico): guide of the simulated profile, the smooth curve of its
median within-hour change (BGRChInt), the input of the recommendation.

Created: 10 May 2023
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    Same procedure as InVivo/13.InterpolationRChZenodo.py: one node per hour
    at minute :59 over 4 repeated days; non-green hours outside the
    25th-75th percentile of those hours set aside and linearly interpolated;
    light smoothing spline (factor 0.1); the second day is kept.

Inputs
    processed/<id>/ComparisonJoinedNoActivity<id2>.csv   (step 12)

Output
    processed/<id>/SampleJoined<id2>.csv   input columns + BGRChInt (mg/dL)

Notes
    - In silico every hour has reliability 3 (step 10, one simulated day),
      so no hour is set aside: the trimming is in the code but has no effect
      here, and the guide is the spline of all 24 hourly medians.
    - Uses np.percentile (np.nanpercentile in InVivo); the simulated series
      has no gaps, so both give the same result.
    - The evaluation grid np.linspace(0, 5760, 5760) has a spacing slightly
      above 1 minute (see InVivo); negligible.
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
# --- Configurable global variable ---
id=globals.id;
print(id)
id2=globals.id2;
print(id2)
# path2: processed/<id>/. Input: the joined table of step 12.
path2=globals.fileToSave;
fileToRead="ComparisonJoinedNoActivity"+str(id2);
# fileToRead="ComparisonJoinedPeakNoActivity"+str(id);
fileToSave="SampleJoined"+str(id2);
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

# One node per hour, at minute :59 (j % 60 == 59), over the four days:
# 96 nodes. j = minute of the day (back to 0 every 1,440); i = minute over
# the four days (the x of the node).
i=0;
j=0;
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

# In silico all hours are green (one simulated day), so nothing is trimmed.
# SampleL: the nodes of hours that are not of high reliability (flag 1 or 2).
# If there are any, the interquartile trimming is applied to them;
# otherwise (always in silico) Sample_ stays equal to Sample.
SampleL = pd.DataFrame(Sample)
Sample_=SampleL
condition = SampleL['medFlag'] ==3;
SampleL = SampleL[~condition]
if len(SampleL)>0:

       # -----------------------------------------------------------#
       #                    Interquartile trimming of the non-green hours
       # -----------------------------------------------------------#

       # 25th, 50th and 75th percentiles of the median change over those nodes
       # (the pandas version is computed too, but not used).
       percentiles = SampleL['FRcH'].quantile([0.25, 0.5, 0.75])
       percentiles_np = np.percentile(SampleL['FRcH'], [25, 50, 75])
       print(percentiles_np[2])

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
       # interpolated below.
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

# Smoothing spline through the 96 nodes, evaluated on 5,760 points
# (four days).
xvals = np.linspace(0, 5760, 5760);

X_Y_Spline =  UnivariateSpline(medIndex, RChToBeInt);
# X_Y_Spline =  UnivariateSpline(medIndex, medValue);
X_Y_Spline.set_smoothing_factor(factor)
Y_ = X_Y_Spline(xvals);
# Interpolation=np.interp(xvals,medIndex,RChToBeInt);
# Keep the second day (points 1439-2878) as the guide BGRChInt: away from
# the ends of the four days, where a spline bends. One value per minute.
Interpolationdf['Key']=data['Key'];
Interpolationdf['BGRChInt']=Y_[1439:2879];
# # -----------------------------------------------------------#
# #                     Merge interpolation
# # -----------------------------------------------------------#
Interpolationdf['Key']=Interpolationdf['Key'].str.strip();
# Add BGRChInt to the table of step 12 and save it as SampleJoined<id2>.csv,
# the input of step 14.
output = pd.merge(data,Interpolationdf,on='Key',how='left');
# # -----------------------------------------------------------#
# #                     Saving
# # -----------------------------------------------------------#
output.to_csv(str(path2)+str(fileToSave)+".csv",index=False);
