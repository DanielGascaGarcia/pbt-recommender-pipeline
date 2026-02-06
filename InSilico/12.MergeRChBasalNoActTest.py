#Code: 12.MergeRChBasalNoActTest.py
#Description: Merge of values.
#Created 10th May 2023
#Author: mbaxdg6


import pandas as pd
import os
from matplotlib import pyplot as plt
import numpy as np
import matplotlib
matplotlib.rcParams.update({'font.size': 15})
import globals

# -----------------------------------------------------------#
# Configuration variables
# -----------------------------------------------------------#

id=globals.id;
print(id)
id2=globals.id2;
print(id2)
path2=globals.fileToSave;
fileToRead1="BGHourRelativeChange"+str(id2);
fileToRead2="BasalSimulated"+str(id2);
fileToSave="ComparisonJoinedNoActivity"+str(id2);
Sampling_time=0.1;

# -----------------------------------------------------------#
# reading two csv files
# -----------------------------------------------------------#

data1 = pd.read_csv(str(path2)+str(fileToRead1)+str("0To24")+"medians"+"_wCN"+".csv");
data2 = pd.read_csv(str(path2)+str(fileToRead2)+".csv");

data1['Key']=data1['Key'].str.strip();
# print(data1);
data2['Key']=data2['Key'].str.strip();
# print(data2);

# using merge function by setting how='left'
output1 = pd.merge(data1,data2,on='Key',how='left');

output1['BasalInfused'].fillna(method='ffill', inplace=True);
output2=output1.interpolate(limit=5, limit_direction="forward");
output2.to_csv(str(path2)+str(fileToSave)+".csv",index=False);

# -----------------------------------------------------------#
# Conversion to arrays
# -----------------------------------------------------------#
Key=[];
MedRelChange=[];
ActiveInsulin=[];
BasalInfused=[];
Reliability=[];

Key=output2["Key"].to_numpy();
MedRelChange=output2["MedRelChange"].to_numpy();
ActiveInsulin=output2["ActiveInsulin"].to_numpy();
BasalInfused=output2["BasalInfused"].to_numpy();
Reliability=output2["Flag"].to_numpy();


T_Key=[];
T_MedRelChange=[];
T_ActiveInsulin=[];
T_BasalInfused=[];
T_Reliability=[];

# Sampling
for i in range(len(Key)):
    # print(i);
    (h, m, s) = Key[i].split(':');
    result = (int(h) * 3600 + int(m) * 60 + int(s))/3600;
    if i % int(Sampling_time*60) ==True:
        T_Key.append(result);
        T_MedRelChange.append(MedRelChange[i]);
        T_ActiveInsulin.append(ActiveInsulin[i]);
        T_BasalInfused.append(BasalInfused[i]);
        T_Reliability.append(Reliability[i]);


# -----------------------------------------------------------#
#                    Generation of levels
# -----------------------------------------------------------#
# Blood Glucose
col =np.where(np.array(T_Reliability)==1,"Red",np.where(np.array(T_Reliability)==2,"Yellow","Green"));
colordf=pd.DataFrame(col,columns=["Color"]);
print(colordf);


# -----------------------------------------------------------#
#                    Graph in general
# -----------------------------------------------------------#
fig, (ax1,ax2)= plt.subplots(nrows=2, sharex=True);
plt.suptitle("Blood Glucose Dynamic, ID: "+str(id2));
# -----------------------------------------------------------#
#                    Graph Insulin
# -----------------------------------------------------------#
ax1.set_ylabel("Basal Insulin (U)");
ax1.axhline(linewidth=2, color='Black');
ax1.plot(T_Key,T_ActiveInsulin, 'o',label='Simulated Action Profile', color="blue");
ax1.plot(T_Key,T_BasalInfused, 'o--',label='Preprogrammed Basal Infusion Rate',color="Orange");
ax1.grid(which='major', color='#DDDDDD', linewidth=0.8);
ax1.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5);
major_ticks = np.arange(0, 24, 5)
minor_ticks = np.arange(0, 24, 1)
ax1.set_xticks(major_ticks)
ax1.set_xticks(minor_ticks, minor=True)
ax1.legend(bbox_to_anchor = (0.786, 1.035), loc='upper left');
# -----------------------------------------------------------#
#              Graph Relative Blood Glucose
# -----------------------------------------------------------#
T_MedRelChange_=[i  for i in T_MedRelChange]
ax2.plot(T_Key,T_MedRelChange_, 'o--',color="Black");
ax2.axhline(linewidth=2, color='Black');
ax2.set_ylabel("BG Rel. Change \n (mg/dL) (mmol/L)");
ax2.grid(which='major', color='#DDDDDD', linewidth=0.8);
ax2.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5);
ax2.set_xlabel("Time (h)");
x=0;
y=0;
z=0;
for i in range (len(T_Key)):
    if T_Reliability[i]==1:
        if x==0:
            ax2.plot(T_Key[i],T_MedRelChange_[i],'o',label='Low reliabilty of BG', color=col[i]);
            x=x+1;
        else: 
            ax2.plot(T_Key[i],T_MedRelChange_[i],'o', color=col[i]);            
    elif T_Reliability[i]==2:
        if y==0:
            ax2.plot(T_Key[i],T_MedRelChange_[i],'o',label='Medium reliabilty of BG', color=col[i]);
            y=y+1;
        else: 
            ax2.plot(T_Key[i],T_MedRelChange_[i],'o', color=col[i]);
    else:
        if z==0:
            ax2.plot(T_Key[i],T_MedRelChange_[i],'o',label='High reliabilty of BG', color=col[i]);
            z=z+1;
        else: 
            ax2.plot(T_Key[i],T_MedRelChange_[i],'o', color=col[i]);


# -----------------------------------------------------------#
#              Reordering the labels
# -----------------------------------------------------------#

handles, labels = ax2.get_legend_handles_labels();
# specify order
order = [];  
# print(handles)
if len(labels)==1:
    if labels[0]=="Low reliabilty of BG":
       order.append(0)
    elif labels[0]=="Medium reliabilty of BG":
        order.append(1);
    else:
        order.append(2);
    ax2.legend(bbox_to_anchor = (0.875, 1.035), loc='upper left');

     
else:
    if labels[0]=="Low reliabilty of BG" and len(order)==0:
        order.append(0);
    elif labels[1]=="Low reliabilty of BG" and len(order)==0:
        order.append(1);
    else:
        order.append(2);
    

    if labels[0]=="Medium reliabilty of BG" and len(order)==1:
        order.append(0);
    elif labels[1]=="Medium reliabilty of BG" and len(order)==1:
        order.append(1);
    else:
        order.append(2);


    if labels[0]=="High reliabilty of BG" and len(order)==2:
        order.append(0);
    elif labels[1]=="High reliabilty of BG" and len(order)==2:
        order.append(1);
    else:
        order.append(2);

    # ax2.legend([handles[idx] for idx in order],[labels[idx] for idx in order],bbox_to_anchor = (0.875, 1.035), loc='upper left');

plt.show();



