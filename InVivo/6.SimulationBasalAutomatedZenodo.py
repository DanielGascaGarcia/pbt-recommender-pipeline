"""
6.SimulationBasalAutomatedZenodo.py   (header of the original file reads S.SimulationBasal.py)
Step 6 (InVivo, basal branch): turn the representative basal profile into an
insulin action curve over the day.

Created: 22 March 2022
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Samples ModeBasalValue every 5 minutes and treats each sample as a
       small dose (rate / 12 U).
    2. Gives each dose a Rayleigh-shaped action profile for rapid-acting
       insulin (scale 1 h, 7 h long) and adds all of them up.
    3. Folds the action that falls after midnight back onto the start of the
       day, so the day behaves as a repeating 24-h cycle.
    4. Saves, every 5 minutes, the summed action (ActiveInsulin) and the
       programmed rate (BasalInfused).

Inputs
    globals.id, globals.fileToSave
    processed/<id>/BasalImputed<id>.csv   (5.FillGapsBasalZenodo.py)

Output
    processed/<id>/BasalSimulated<id>.csv   Key (every 5 min), ActiveInsulin, BasalInfused

Notes
    - Every dose uses insulin kind 1 (rapid-acting); the other kinds in
      InsulinDict are defined but not used.
    - The samples are taken where i % 5 == True, i.e. at minutes 1, 6, 11, ...
      (one minute after the 5-min marks); the time of each dose is shifted
      back by 1 min to compensate.
    - This curve is used for the figure of 12.MergeRChBasalNoAct and to
      describe the programmed profile; it does not enter the basal
      recommendation.
    - In the block that pads IF_F_Offset to 288 samples, the else branch
      loops over a negative range and does nothing; it is never needed with
      a 24-h profile.
    - The plot is commented out.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import rayleigh
from scipy.stats import lognorm 
import pandas as pd
from datetime import datetime,timedelta
import datetime 
import os
import matplotlib
matplotlib.rcParams.update({'font.size': 12})

import globals
id=globals.id;

# -----------------------------------------------------------#
# Parameters
# -----------------------------------------------------------#

# path2: processed/<id>/ of the participant.
path2=globals.fileToSave;
fileToRead="BasalImputed"+str(id)+".csv";
fileToSave="BasalSimulated"+str(id)+".csv";



# Insulin types, kept for reference. Basal uses type 1 (rapid-acting, what
# the pump delivers).
InsulinDict = { "Rapid":1,"Regular": 2,"NPH": 3,"Gargline/Determine": 4}    

                                                                                   #Units to show either mmol/L or mg/dL
t_start=[0];                                                                       #Time to start the simulation in hrs.
# Representative basal profile of step 5: Key (each minute) and
# ModeBasalValue (U/h).
data= pd.read_csv(str(path2)+fileToRead);
t = data["Key"];
InsulinMode=data["ModeBasalValue"];
II=[];                                                                             #Insulin Infused in Units  [U].
InsulinV=[];                                                                       #Insulin type of each dose (1 = rapid-acting).   
t_insulin=[];                                                                      #Time of each dose, in hours.         
Sampling_time=5/60;                                                                #Sampling time in hrs
Basal_infused=[];
# -----------------------------------------------------------#
#Generation of input variables
# -----------------------------------------------------------#
# One dose every 5 min: rate (U/h) / 12.
# 'i % 5 == True' is True when i % 5 == 1 (True equals 1): minutes 1, 6,
# 11, ... Each dose = rate (U/h) / 12, the insulin of 5 minutes; its time in
# hours is moved back 1 minute (0:00, 0:05, ...).
for i in range(len(t)):
    # print(i);
    (h, m, s) = t[i].split(':');
    result = (int(h) * 3600 + int(m) * 60 + int(s))/3600;
    if i % int(Sampling_time*60) ==True:
        t_insulin.append(result-1/60);
        InsulinV.append(1);
        II.append(InsulinMode[i]/12);

# BasalInfused: the rate (U/h) at the same minutes, kept for the output.
for i in range(len(t)):
    if i % 5==True:
       Basal_infused.append(InsulinMode[i]);
# -----------------------------------------------------------#
# Insulin part
# -----------------------------------------------------------#
#Maximum array size to fill up with 0s
# -----------------------------------------------------------#
# Length of the action matrix. Each dose starts at its own 5-min slot
# (int(12*t)+1 zeros before it) and its profile lasts 85 points for
# rapid-acting insulin (7 h at 5 min), 109 regular, 193 NPH, 289
# glargine/detemir. FP = the longest row.
Size= [];
for i in range(len(II)):    
    T_0 = [];
    for j in range(int(12*t_insulin[i])+1):
        T_0.append(0);
    T_BB=np.array(T_0);
    if InsulinV[i]==1:
        Size.append(len(T_BB)+85);
    elif InsulinV[i]==2:   
        Size.append(len(T_BB)+109);
    elif InsulinV[i]==3:
        Size.append(len(T_BB)+193);
    elif InsulinV[i]==4:
        Size.append(len(T_BB)+289);
    else:
        print("Not a valid value for kind of insulin");
    FP=max(Size);
  
# I_MAT: one row per dose, one column per 5-minute slot; zeros to begin.
I_MAT=np.full((len(II), FP), 0,dtype=float);

# print(I_MAT);

# -----------------------------------------------------------#
# Insulin doses computation 
# -----------------------------------------------------------#
# Fill each row: zeros until the dose, its action profile, then zeros up to
# length FP.
for i in range(len(II)): 
    if InsulinV[i]==1:   
        # Rapid-acting: action as a Rayleigh density (scale 1 h) over 7 h
        # (85 points), times the dose.
        T_0 = [];
        for j in range(int(12*t_insulin[i])+1):
            T_0.append(0);
        T_BB=np.array(T_0);
        T_D = np.linspace(0,7,85);
        a, b = 0, 1
        dist=rayleigh(a, b); 
        FFI=dist.pdf(T_D);
        BIE =II[i]*FFI;  
        BIEF=np.concatenate((T_BB,BIE),axis=0);
        T_0 = [];
        for j in range(FP-len(BIEF)):
            T_0.append(0);
        T_OF=np.array(T_0); #Correction.
        BIEFF=np.concatenate((BIEF,T_OF),axis=0);    
    # Types 2-4: same pattern with longer profiles. Not used for basal.
    if InsulinV[i]==2:   
        T_0 = [];
        for j in range(int(12*t_insulin[i])+1):
            T_0.append(0);
        T_BB=np.array(T_0);
        T_D = np.linspace(0,9,109);
        a, b = 0, 2.5
        dist=rayleigh(a, b); 
        FFI=dist.pdf(T_D);
        BIE =II[i]*FFI;  
        BIEF=np.concatenate((T_BB,BIE),axis=0);
        T_0 = [];
        for j in range(FP-len(BIEF)):
            T_0.append(0);
        T_OF=np.array(T_0); #Correction.
        BIEFF=np.concatenate((BIEF,T_OF),axis=0);    
    if InsulinV[i]==3:   
        T_0 = [];
        for j in range(int(12*t_insulin[i])+1):
            T_0.append(0);
        T_BB=np.array(T_0);
        T_D = np.linspace(0,16,193);
        a, b = 0, 5
        dist=rayleigh(a, b); 
        FFI=dist.pdf(T_D);
        BIE =II[i]*FFI;  
        BIEF=np.concatenate((T_BB,BIE),axis=0);
        T_0 = [];
        for j in range(FP-len(BIEF)):
            T_0.append(0);
        T_OF=np.array(T_0); #Correction.
        BIEFF=np.concatenate((BIEF,T_OF),axis=0);    
    if InsulinV[i]==4:   
        T_0 = [];
        for j in range(int(12*t_insulin[i])+1):
            T_0.append(0);
        T_BB=np.array(T_0);
        T_D = np.linspace(0,24,289);
        a, b = 0, 6
        dist=rayleigh(a, b); 
        FFI=dist.pdf(T_D);
        BIE =II[i]*FFI;  
        BIEF=np.concatenate((T_BB,BIE),axis=0);
        T_0 = [];
        for j in range(FP-len(BIEF)):
            T_0.append(0);
        T_OF=np.array(T_0); #Correction.
        BIEFF=np.concatenate((BIEF,T_OF),axis=0);    
    # Store the row of this dose.
    I_MAT[i,]=BIEFF;    
# Total insulin action at each 5-min slot: sum over every dose.
I_MATF=I_MAT.sum(axis=0);
# print(I_MATF);

# -----------------------------------------------------------#
# Graph
# -----------------------------------------------------------#
# T: time of each slot, in hours.
T=np.linspace(0,int(5*len(I_MATF)),len(I_MATF))/60;

T_F=[];
IF_F=[];

# for i in range(int(12*t_start[0]),len(T)-1):
# Copy every slot but the last.
for i in range(len(T)-1):
    T_F.append(T[i]);
    IF_F.append(I_MATF[i]);
    
# Make Basal_infused as long as T_F: pad with 0, or drop from the end.
if len(T_F)-len(Basal_infused)>0:
    for j in range(len(T_F)-len(Basal_infused)):
                Basal_infused.append(0);
else:
    for j in range(len(Basal_infused)-len(T_F)):
                del Basal_infused[-1];


# Action after midnight (beyond 288 samples) is added back to the start of the day.
IF_F_Offset=[];
for i in range(len(T_F)-288):
    IF_F_Offset.append(IF_F[i+288]);

# ... and the series are cut to one day (288 slots).
for i in range(len(T_F)-288):
    del Basal_infused[-1];
    del T_F[-1];
    del IF_F[-1];


# Pad IF_F_Offset with zeros up to 288 values.
if 288-len(IF_F_Offset)>0:
    for j in range(288-len(IF_F_Offset)):
        IF_F_Offset.append(0);
else:
    for j in range(288-len(IF_F_Offset)):
        del IF_F_Offset[-1];


# Lengths printed as a check (all 288).
print(len(T_F));
print(len(Basal_infused));
print(len(IF_F));
print(len(IF_F_Offset));
# Active insulin of the day = action of the day + action carried over from
# the previous day (the same profile repeats every day).
IF_F = np.add(IF_F, IF_F_Offset);  

# -----------------------------------------------------------#
# Units
# -----------------------------------------------------------#

# Figure (commented out).
# plt.ylabel("Insulin (U)");
# plt.xlabel("Time (h)");
# plt.title("Basal Insulin Dynamic");
# plt.plot(T_F,IF_F, 'o',label='Active Insulin', color="blue");
# plt.plot(T_F,Basal_infused, 'o',label='Basal insulin values',color="Brown");
# plt.ylim([0, 3]);
# plt.grid(which='major', color='#DDDDDD', linewidth=0.8);
# plt.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5);

# plt.legend();
# # # Show the plot
# plt.show();


# -----------------------------------------------------------#
# Save values
# -----------------------------------------------------------#
# Output: one row every 5 minutes (Key 00:00:00, 00:05:00, ...).
df = pd.DataFrame();
di = datetime.datetime(2010, 12, 1);
end = datetime.datetime(2010, 12, 1, 23, 59, 59);
step = datetime.timedelta(minutes=5);
secArray=[];
# -----------------------------------------------------------#
# Generate key
# -----------------------------------------------------------#
while di < end:
        secArray.append(str(di.strftime('%H:%M:%S')));
        di += step;
secArray=pd.DataFrame(secArray, columns=['Key']);
df['Key']=secArray;
# -----------------------------------------------------------#
# Save columns
# -----------------------------------------------------------#
# Columns: ActiveInsulin (summed action; used by the figure of step 12) and
# BasalInfused (programmed rate, U/h).
IF_F=pd.DataFrame(IF_F, columns=['ActiveInsulin']); 
Basal_infused=pd.DataFrame(Basal_infused, columns=['BasalInfused']); 
df['ActiveInsulin']=IF_F;
df['BasalInfused']=Basal_infused;
df.to_csv(str(path2)+str(fileToSave),index=False);
