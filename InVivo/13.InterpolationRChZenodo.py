#Code: 13.InterpolationRChZenodo.py
#Description: Merge of values.
#Created 10th May 2023
#Author: mbaxdg6


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
# Configuration variables
# -----------------------------------------------------------#
import globals
id=globals.id;

path2= globals.fileToSave;
fileToRead="ComparisonJoinedNoActivity"+str(id);
# fileToRead="ComparisonJoinedPeakNoActivity"+str(id);
fileToSave="SampleJoined"+str(id);
data = pd.read_csv(str(path2)+str(fileToRead)+".csv");

dt = datetime.datetime(2010, 12, 1);
end = datetime.datetime(2010, 12, 4, 23, 59, 59);
step = datetime.timedelta(minutes=1);


# -----------------------------------------------------------#
#                           Sample
# -----------------------------------------------------------#
factor=0.1
Sample=pd.DataFrame();   
medTime=[];
medValue=[];
medIndex=[];
medFlag=[];

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
Sample['Key']=medTime;
Sample['FRcH']=medValue;
Sample['FRcH'].fillna('');
Sample['medFlag']=medFlag;
Sample['medFlag'].fillna('');
# -----------------------------------------------------------#
#                    Keep the least reliable
# -----------------------------------------------------------#

SampleL = pd.DataFrame(Sample)
Sample_=SampleL
condition = SampleL['medFlag'] ==3;
SampleL = SampleL[~condition]
if len(SampleL)>0:

       # -----------------------------------------------------------#
       #                    Small outlier detection
       # -----------------------------------------------------------#

       percentiles = SampleL['FRcH'].quantile([0.25, 0.5, 0.75])
       percentiles_np = np.nanpercentile(SampleL['FRcH'], [25, 50, 75])
       print(percentiles_np[2])   # 75th percentile
       # -----------------------------------------------------------#
       #                    Filter values and eliminate duplicates
       # -----------------------------------------------------------#
       condition = SampleL['FRcH']<percentiles_np[0];
       SampleL = SampleL[~condition]
       condition = SampleL['FRcH']>percentiles_np[2];
       SampleL = SampleL[~condition]
       SampleL = SampleL.drop_duplicates();

       # # -----------------------------------------------------------#
       # #                     Merge interpolation
       # # -----------------------------------------------------------#
       Merge=pd.DataFrame(); 
       Sample['Key']=Sample['Key'].str.strip();
       SampleL['Key']=SampleL['Key'].str.strip();
       Sample_= pd.merge(Sample,SampleL,on='Key',how='left');


       # -----------------------------------------------------------#
       #                     Replace in original
       # -----------------------------------------------------------#

       # Define the condition for replacement
       condition_ = Sample_['medFlag_x']<3 
       # Replace values in column 'B' where the condition is True
       Sample_.loc[condition_, 'FRcH_x'] = np.nan


       # Define the condition for replacement
       condition__ = Sample_['medFlag_y'].notnull()
       # Replace values in column 'B' where the condition is True
       Sample_.loc[condition__, 'FRcH_x'] = Sample_.loc[condition__, 'FRcH_y']

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
RChToBeInt=Sample_['FRcH'].to_numpy();

# -----------------------------------------------------------#
#                     Linear Interpolation
# -----------------------------------------------------------#



missing_indices = np.isnan(RChToBeInt)
non_missing_indices = ~missing_indices
indices = np.arange(len(RChToBeInt))
RChToBeInt[missing_indices] = np.interp(indices[missing_indices], indices[non_missing_indices], RChToBeInt[non_missing_indices])

# -----------------------------------------------------------#
#                     Spline interpolation
# -----------------------------------------------------------#

xvals = np.linspace(0, 5760, 5760);

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
Interpolationdf['Key']=Interpolationdf['Key'].str.strip();
output = pd.merge(data,Interpolationdf,on='Key',how='left');
# # -----------------------------------------------------------#
# #                     Saving
# # -----------------------------------------------------------#
output.to_csv(str(path2)+str(fileToSave)+".csv",index=False);