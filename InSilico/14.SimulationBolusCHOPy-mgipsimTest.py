"""
14.SimulationBolusCHOPy-mgipsimTest.py   (header of the original file reads 14.SimulationBolusCHO.py)
Step 14 (InSilico): the PBT recommendation. From the guide of the simulated
profile, compute hour by hour the basal change that flattens it, and the
recommended basal profile.

Created: 1 May 2024
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Reads the guide BGRChInt (mg/dL) and the correction factor (ISF,
       mg/dL per U) of the virtual patient.
    2. For each hour of the day (the day repeated three times, hours 20 to
       51), takes the deviation of the guide: positive (basal deficit) or
       negative (basal excess).
    3. Sizes the correction as deviation / ISF, split into 12 equal doses
       over one hour starting 2 h before the deviation, and models its
       effect with the OpenAPS insulin activity curve (duration 600 min,
       peak 60 min). The effect is subtracted (deficit) or added (excess)
       to the guide before the next hour is processed.
    4. Places each dose in the recommended profile LEAD_HOURS (2, globals.py) h before
       the deviation it corrects.
    5. Recommended rate = programmed rate + change. A negative rate is set
       to 0 and the reduction that does not fit is subtracted NEGATIVE_RATE_SHIFT_MIN (120, globals.py) min
       earlier (wrapping to the end of the day), never below 0.
    6. Each hour keeps one value (the first 5 minutes take the value of the
       rest of the hour).

Inputs
    globals.id, globals.id2, globals.path (Py-mgipsim patients), globals.fileToSave
    processed/<id>/SampleJoined<id2>.csv   (step 13; BGRChInt and BasalInfused)
    <path>/<id2>.json   correction_bolus of the virtual patient

Outputs (in processed/<id>/)
    SampledAdvised<id2>_1.csv       guide before and after, change per 5 min
    SampledAdvised<id2>_final.csv   + RecIns, AdjustedRecIns (recommended
                                    rate, U/h), InsChange (change, sign
                                    reversed for the figure)

Notes
    - LEAD_HOURS = 2 places each dose where it was sized (it was applied in
      the hour of the deviation before). The 22-23 h of the profile receive
      the corrections computed for 0-1 h; since each simulated day starts at
      midnight, they do not act on the early hours of the evaluated day.
    - The negative-rate rule subtracts the excess (it added it before,
      which increased insulin); only Man02 was affected.
    - The comment "ISF [mmol/L*U]" is mislabelled: the value is in mg/dL
      per U, consistent with the guide in mg/dL.
    - The figures are shown, not saved; the orchestrator sets the Agg
      backend.
    - The main loop runs once (r = 0); the code for further iterations is
      kept but not used.
"""

import datetime 
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import rayleigh
from scipy.stats import lognorm 
import os
import pandas as pd
import matplotlib
matplotlib.rcParams.update({'font.size': 12})
from scipy.signal import find_peaks
import numpy as np
import json
import csv
import globals
# --- Configurable global variable ---
id=globals.id;
print(id)
id2=globals.id2;
print(id2)
# -----------------------------------------------------------#
#Reading variables
# -----------------------------------------------------------#
# OpenAPS exponential insulin curves: insulin activity (Ia) and insulin on
# board (IOB) for an action duration td and a peak tp (minutes).
def insulin_activity_and_IOB_curve(td, tp, time_points):
    """
    Calculate the insulin activity (Ia) and insulin on board (IOB) curves.
    
    Parameters:
    td (float): Duration of insulin action in minutes.
    tp (float): Peak activity time in minutes.
    time_points (array-like): Array of time points in minutes to evaluate Ia and IOB.

    Returns:
    tuple: Arrays of Ia (insulin activity) and IOB values for each time point.
    """
    # Time constant of exponential decay
    tau = tp * (1 - tp / td) / (1 - 2 * tp / td)
    
    # Rise time factor
    a = 2 * tau / td
    
    # Auxiliary scale factor
    S = 1 / (1 - a + (1 + a) * np.exp(-td / tau))
    
    # Calculate Ia and IOB at each time point
    Ia = (S / tau**2) * time_points * (1 - time_points / td) * np.exp(-time_points / tau)
    IOB = 1 - S * (1 - a) * ((time_points**2 / (tau * td * (1 - a)) - time_points / tau - 1) * np.exp(-time_points / tau) + 1)
    
    return Ia, IOB


# Correction factor of a Py-mgipsim virtual patient (mg/dL per U), read from
# its JSON.
def extract_correction_bolus_from_file(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)
    return data["demographic_info"]["correction_bolus"]

# Example usage
# path: Py-mgipsim patient files; fileJSON: <id2>.json.
path = globals.path;
fileJSON=str(id2)+".json"


# -----------------------------------------------------------#
#File to read
# -----------------------------------------------------------#
# CF: correction factor (ISF) of the virtual patient, in mg/dL per U.
CF = float(extract_correction_bolus_from_file(path+fileJSON));


# path2: processed/<id>/; fileToSave: prefix of the outputs.
path2=globals.fileToSave
fileToSave="SampledAdvised"+str(id2);   
# -----------------------------------------------------------#
#Main loop
# -----------------------------------------------------------#
# Main loop: runs once (r = 0). With r > 0 it would start again from the
# previous result; not used.
for r in range(1):

# -----------------------------------------------------------#
#First cicle
# -----------------------------------------------------------#
    if r==0: 
            fileToRead="SampleJoined"+str(id2)+".csv";
    else:
            fileToRead="SampledAdvised"+str(id2)+"_"+str(r)+".csv";   

    print(fileToRead)
    # -----------------------------------------------------------#
    #Kinds of insulin
    # -----------------------------------------------------------#  
                                                                        #Insulin Infused in Units  [U].
    InsulinDict = { "Rapid":1,
                    "Regular": 2,
                    "NPH": 3,
                    "Gargline/Determine": 4
                }    

    # -----------------------------------------------------------#
    #Reading of file
    # -----------------------------------------------------------#
    data= pd.read_csv(str(path2)+fileToRead);
    t = data["Key"];
    if r==0:
        BGRChInt=data["BGRChInt"];
    else:
        BGRChInt=data["BGFin"];
    # -----------------------------------------------------------#
    #Insulin to set up
    # -----------------------------------------------------------#
    ISF=CF;                                                                         #Insulin sensitivity factor (= CF), mg/dL per U.           
    #144                                                    
    t_start=[0];                                                                       #Time to start the simulation in hrs.
    Units=[1];                                                                         #Kind of units to graph
    Sampling_time=5/60;                                                                #Sampling time in hrs

    # -----------------------------------------------------------#
    # Insulin function
    # -----------------------------------------------------------#

    # get_insulin_type: for each deviation (values, mg/dL) at hour 'peaks', 12
    # equal doses of value / (12 x ISF) U, one every 5 minutes, starting 2 h
    # before the deviation (time = peaks - 2). Returns the doses, their insulin
    # type (1) and their times in hours.
    def get_insulin_type(peaks,values):
        t_ins=np.full((len(peaks), 12), 0,dtype=float);
        IDos=np.full((len(peaks), 12), 0,dtype=float);
        f=1/12; #Sampling time
        g=12; #Adjusting insulin in 12 intakes
        for i in range(len(values)):
            time=peaks[i]-2;  
            t_ins[i,]=[time,time+f*1,time+f*2,time+f*3,time+f*4,time+f*5,time+f*6,time+f*7,time+f*8,time+f*9,time+f*10,time+f*11];   #Time in hrs to bolus.                                                                                                                                    
            IDos[i,]=[values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF),values[i]/(g*ISF)];   
            print("Value at "+str(values[i]));
            print("Insulin at "+str(values[i]/ISF)); 
        t_insulin=[];
        II=[];

        for i in range(len(values)):
            t_insulin=np.concatenate((t_insulin,t_ins[i,]),axis=0);
            II=np.concatenate((II,IDos[i,]),axis=0);
        InsulinV=[]
        for i in range(len(II)):
            InsulinV.append(1);
        return II,InsulinV, t_insulin

    # -----------------------------------------------------------#
    # Curve function
    # -----------------------------------------------------------#
    # get_curve: glucose effect over time of every dose, on a 5-minute grid.
    # Rapid-acting insulin (type 1, the one used): cumulative OpenAPS activity
    # curve (duration 600 min, peak 60 min), resampled to 9 h (109 points) and
    # scaled by dose x ISF (x 20.13, a fixed scaling constant).
    # Types 2-4: Rayleigh curves, not used. Returns the summed effect.
    def get_curve(II,InsulinV,t_insulin):
        Size= [];
        for i in range(len(II)):    
            T_0 = [];
            for j in range(int(12*t_insulin[i])+1):
                T_0.append(0);
            T_BB=np.array(T_0);
            if InsulinV[i]==1:
                Size.append(len(T_BB)+109);
            elif InsulinV[i]==2:   
                Size.append(len(T_BB)+109);
            elif InsulinV[i]==3:
                Size.append(len(T_BB)+145);
            elif InsulinV[i]==4:
                Size.append(len(T_BB)+289);
            else:
                print("Not a valid value for kind of insulin");
            FP=max(Size);
        
        I_MAT=np.full((len(II), FP), 0,dtype=float);
        # -----------------------------------------------------------#
        # Insulin doses computation 
        # -----------------------------------------------------------#
        for i in range(len(II)): 
            # print(InsulinV[i]);
            if InsulinV[i]==1:   
                T_0 = [];
                for j in range(int(12*t_insulin[i])+1):
                    T_0.append(0);
                T_BB=np.array(T_0);
                # Parameters in minutes
                td = 600    # Duration of action (in minutes)
                tp = 60     # Peak activity time (in minutes)
                time_points_minutes = np.arange(0, td + 1, 5)  # Array of time points every 5 minutes

                # Convert time_points to hours for plotting
                time_points_hours = time_points_minutes / 60

                # Calculate Ia and IOB values
                Ia, IOB = insulin_activity_and_IOB_curve(td, tp, time_points_minutes)
                # Scale up Ia by 100 times for altitude adjustment
                Ia_scaled = Ia * 100

                # Calculate cumulative distribution of Ia (using trapezoidal integration for approximation)
                cumulative_Ia = np.cumsum(Ia_scaled) * np.diff(time_points_minutes, prepend=0)

                # Define the time array T_D for 9 hours with 5-minute intervals (109 points)
                T_D = np.linspace(0, 9, 109)

                # Rescale FFI to fit the T_D array using linear interpolation
                FFI = np.interp(T_D, time_points_hours, cumulative_Ia) / 100
                BIE =II[i]*20.13*ISF*FFI;  
                BIEF=np.concatenate((T_BB,BIE),axis=0);
                T_0 = [];
                for j in range(FP-len(BIEF)):
                    T_0.append(0);
                T_OF=np.array(T_0); #Correction.
                BIEFF=np.concatenate((BIEF,T_OF),axis=0);    
            if InsulinV[i]==2:   
                T_0 = [];
                for j in range(int(12*t_insulin[i])+1):
                    T_0.append(0);
                T_BB=np.array(T_0);
                T_D = np.linspace(0,9,109);
                a, b = 0, 2.5
                dist=rayleigh(a, b); 
                FFI=dist.cdf(T_D);
                BIE =II[i]*7.53416*ISF*FFI;  
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
                T_D = np.linspace(0,14,145);
                a, b = 0, 5
                dist=rayleigh(a, b); 
                FFI=dist.cdf(T_D);
                BIE =II[i]*3.7670*ISF*FFI;  
                BIEF=np.concatenate((T_BB,BIE),axis=0);
                T_0 = [];
                for j in range(FP-len(BIEF)):
                    T_0.append(0);
                T_OF=np.array(T_0); #Correction.
                BIEFF=np.concatenate((BIEF,T_OF),axis=0);    
            if InsulinV[i]==4:   
                T_0 = [];
                for j in range(int(4*t_insulin[i])+1):
                    T_0.append(0);
                T_BB=np.array(T_0);
                T_D = np.linspace(0,24,289);
                a, b = 0, 6
                dist=rayleigh(a, b); 
                FFI=dist.cdf(T_D);
                BIE =II[i]*3.1392*ISF*FFI;  
                BIEF=np.concatenate((T_BB,BIE),axis=0);
                T_0 = [];
                for j in range(FP-len(BIEF)):
                    T_0.append(0);
                T_OF=np.array(T_0); #Correction.
                BIEFF=np.concatenate((BIEF,T_OF),axis=0);    
            I_MAT[i,]=BIEFF;    
        I_MATF=I_MAT.sum(axis=0);
        return I_MATF

    # -----------------------------------------------------------#
    # Homologation of sizes function
    # -----------------------------------------------------------#
    # homologation: pads the shorter of two arrays with zeros, so both have the
    # same length.
    def homologation(Array1,Array2):
        if len(Array1)-len(Array2)>0:
            T_0 = [];
            for j in range(len(Array1)-len(Array2)):
                T_0.append(0);
            T_0F=np.array(T_0);
            Array2=np.concatenate((Array2,T_0F),axis=0);  
            
        elif len(Array2)-len(Array1)>0:
            T_0 = [];
            for j in range(len(Array2)-len(Array1)):
                T_0.append(0);
            T_0F=np.array(T_0);
            Array1=np.concatenate((Array1,T_0F),axis=0);  
        else:
            print("Same longitud");
        return Array1,Array2

    # -----------------------------------------------------------#
    # Gradient on Insulin function
    # -----------------------------------------------------------#
    # gradient: change between consecutive slots (the effect added in each
    # 5-minute slot).
    def gradient(I_MATF):
        GI_MATF=[];
        for i in range(len(I_MATF)-1):
            GI_MATF.append(I_MATF[i+1]-I_MATF[i]);
        return GI_MATF


    # -----------------------------------------------------------#
    #Generation of input variables
    # -----------------------------------------------------------#
    # -----------------------------------------------------------#
    # Blood glucose Relative Change
    # -----------------------------------------------------------#


    # Hour loop. The guide (one value every 5 min, 288 per day) is repeated
    # three times (72 h). Hours k = 20 to 51 are processed in order, each one
    # starting from the guide as corrected by the hours before (BGF_F).
    BGF_F=[];
    BG_initial=[];
    range_i=20 
    range_f=52
    Insulin_ch=[];
    for k  in range(range_i,range_f):
        # print(k-range_i)
        BG_MATF=[];
        t_BGRChInt=[];
        # First pass (k = 20): sample the guide every 5 min (minutes 1, 6, 11, ...)
        # into BG_MATF and keep a copy in BG_initial. Later passes start from the
        # corrected guide BGF_F.
        for i in range(len(t)):
            # print(i);
            (h, m, s) = t[i].split(':');
            result = (int(h) * 3600 + int(m) * 60 + int(s))/3600;
            if i % int(Sampling_time*60) ==True:
                t_BGRChInt.append(result-1/60);
                if k==range_i:
                    BG_MATF.append(BGRChInt[i]);
                    BG_initial.append(BGRChInt[i]);
                else: 
                    BG_MATF=BGF_F;
        
        # Three copies of the day.
        BG_MATF = np.concatenate([BG_MATF,BG_MATF,BG_MATF])
    # -----------------------------------------------------------#
    # Gradient on Insulin
    # -----------------------------------------------------------#
        # Split into positive part (guide above 0: basal deficit) and negative part
        # (guide below 0: basal excess), both as positive numbers.
        BG_MATF_P=np.linspace(0,0,range_f*12);
        BG_MATF_N=np.linspace(0,0,range_f*12);
        # print(len(BG_MATF))
        for i in range(range_f*12):
            if BG_MATF[i]>0:
                BG_MATF_P[i]=BG_MATF[i];
            elif BG_MATF[i]<0:
                BG_MATF_N[i]=(-1)*BG_MATF[i];
            else:
                pass
        # if k==range_v:
        #     BG_0=BGRChInt[0];                                                                  #Initial Blood Glucose [mmol/L].
        # else:
        # BG_0: first value, used to start the corrected series.
        BG_0=BG_MATF[0];


        # Deviation at hour k (slot 12 x k). Positive -> add insulin; otherwise
        # (negative or zero) -> remove insulin.
        if  BG_MATF_P[12*k]>0:
            flag=BG_MATF_P[k];
            values=[BG_MATF_P[12*k]]
            peaks=[k];
        # -----------------------------------------------------------#
        # -----------------------------------------------------------#
        # Compute insulin positive part
        # -----------------------------------------------------------#
        # -----------------------------------------------------------#    
            # Doses that would correct it; stored (positive) in Insulin_ch, 12 per hour.
            II_P,InsulinV_P,t_insulin_P=get_insulin_type(peaks,values);

            #Add each element
            for element in II_P:
                Insulin_ch.append(element)
        # -----------------------------------------------------------#
        # Call function positive part
        # -----------------------------------------------------------#
            # Their glucose-lowering effect over time.
            I_MATF_P=get_curve(II_P,InsulinV_P,t_insulin_P);

        # -----------------------------------------------------------#
        # Call homologation
        # -----------------------------------------------------------#
            I_MATF_P,BG_MATF=homologation(I_MATF_P,BG_MATF);

        # -----------------------------------------------------------#
        # Call gradient
        # -----------------------------------------------------------#
            # Effect added per 5-min slot (negative increments set to 0 below).
            GI_MATF_P=gradient(I_MATF_P);

        # -----------------------------------------------------------#
        # Graph
        # -----------------------------------------------------------#
            # Corrected guide: the effect of the extra insulin is subtracted slot by
            # slot. BGF = corrected guide; BF = guide before this hour; GPP = effect per
            # slot; IF = insulin effect alone.
            BGF=[];
            IF=[];
            BF=[];
            GPP=[];
            for i in range(len(GI_MATF_P)):
                if GI_MATF_P[i]<0:
                    GI_MATF_P[i]=0;
                if i==0:
                    BGF.append(BG_0); 
                    IF.append(BG_0); 
                    BF.append(BG_0); 
                    GPP.append(BG_0);
                BGF.append(BG_MATF[i]-GI_MATF_P[i]);
                IF.append(IF[i]-GI_MATF_P[i]);
                BF.append(BG_MATF[i]);
                GPP.append(GI_MATF_P[i]);       
            # plt.plot(GI_MATF_P[288:576], 'o')
        else:
            # Negative deviation: the same steps for the reduction. Its doses are stored
            # as negative in Insulin_ch, and their effect is added to the guide (less
            # insulin -> glucose higher).
            flag=BG_MATF[12*k];
            values=[BG_MATF_N[12*k]]
            peaks=[k];  
        # -----------------------------------------------------------#
        # -----------------------------------------------------------#
        # Compute insulin negative part
        # -----------------------------------------------------------#
        # -----------------------------------------------------------#
            II_N,InsulinV_N,t_insulin_N=get_insulin_type(peaks,values);

            #Add each element
            for element in II_N:
                Insulin_ch.append(-1*element)
    

        # -----------------------------------------------------------#
        # Call function negative part
        # -----------------------------------------------------------#
            I_MATF_N=get_curve(II_N,InsulinV_N,t_insulin_N);

        # -----------------------------------------------------------#
        # Call homologation
        # -----------------------------------------------------------#
            I_MATF_N,BG_MATF=homologation(I_MATF_N,BG_MATF);
    
        # -----------------------------------------------------------#
        # Call gradient
        # -----------------------------------------------------------#
            GI_MATF_N=gradient(I_MATF_N);     

        # -----------------------------------------------------------#
        # Graph
        # -----------------------------------------------------------#
            BGF=[];
            IF=[];
            BF=[];
            GPP=[];
            for i in range(len(GI_MATF_N)):

                if GI_MATF_N[i]<0:
                    GI_MATF_N[i]=0;
                if i==0:
                    BGF.append(BG_0); 
                    IF.append(BG_0); 
                    BF.append(BG_0); 
                    GPP.append(BG_0);
                BGF.append(BG_MATF[i]+GI_MATF_N[i]);
                IF.append(IF[i]+GI_MATF_N[i]);
                BF.append(BG_MATF[i]);  
                GPP.append(GI_MATF_N[i]);  
            # plt.plot(GI_MATF_N[288:576], 'o')     
        # Time axis (hours) and the series cut to the processed span: BGF_F is
        # the corrected guide passed to the next hour, the rest feed the figures.
        T=np.linspace(0,int(5*len(BGF)),len(BGF))/60;
        # -----------------------------------------------------------#
        # Sampling for graphs
        # -----------------------------------------------------------#
        T_=[]
        for i in range(len(T)):
            if T[i]<=(range_f-1):
                T_.append(T[i]);
        T_F=[];
        IF_F=[];
        BF_F=[];
        BGF_F=[];
        BG_MATF_N_F=[]
        BG_MATF_P_F=[]
        GPP_F=[]
        for i in range(int(12*t_start[0]),len(T_)):
            T_F.append(T[i]);
            IF_F.append(IF[i]);
            BF_F.append(BF[i+1]);
            BGF_F.append(BGF[i+1]);
            BG_MATF_N_F.append(BG_MATF_N[i]);
            BG_MATF_P_F.append(BG_MATF_P[i]);
            GPP_F.append(GPP[i]);    


        
        # Figures of each hour (commented out).
        # # -----------------------------------------------------------#
        # # Units
        # # -----------------------------------------------------------#
        # if Units[0]==1:
        #     plt.ylabel("Blood Glucose (mg/dL)");
        #     plt.xlabel("Time (h)");
        #     plt.title("Blood Glucose Dynamic ID="+str(id2)+", cycle: "+str(r+1));
        #     # plt.plot(T_F,IF_F, 'o',label='Insulin effect alone', color="blue");
        #     plt.plot(T_F[0:288],np.concatenate([BG_initial,BG_initial,BG_initial[0:276]])[288:576], 'o',label='Original BG relative change',color="Green");   
        #     plt.plot(T_F[0:288],BF_F[288:576], 'o',label='BG relative change -1 h',color="Orange"); 
        #     plt.plot(T_F[0:288],BGF_F[288:576], 'o',label='Current BG relative change',color="Red");
        #     plt.plot(T_F[0:288],GPP_F[288:576], 'o',label='Gradient',color="Brown");
        #     # plt.plot(T_F,BG_MATF_P_F, 'o',label='Blood Glucose, positive part',color="Gray");
        #     # plt.plot(T_F,BG_MATF_N_F, 'o',label='Blood Glucose, negative part',color="Brown");
        #     plt.axhline(linewidth=2, color='Black');

        #     if flag>=0:
        #         plt.plot(peaks[0]-24,values[0], 'X',label='Positive peak',color="yellow");
        #     else:
        #         plt.plot(peaks[0]-24,(-1)*values[0], 'X',label='Negative peak',color="blue");    
        #     # plt.ylim([-30, 30]);
        #     plt.grid(which='major', color='#DDDDDD', linewidth=0.8);
        #     plt.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5);
        #     plt.minorticks_on();
        #     plt.legend();
        #     # # Show the plot
        #     plt.show();
        # else:
        #     plt.ylabel("Blood Glucose (mmol/L)");
        #     plt.xlabel("Time (h)");
        #     plt.title("Blood Glucose Dynamic ID="+str(id2)+", cycle: "+str(r+1));
        #     plt.plot(T_F[0:288],[i / 18 for i in np.concatenate([BG_initial,BG_initial,BG_initial[0:276]])[288:576]], 'o',label='Original BG relative change',color="Green");   
        #     plt.plot(T_F[0:288],[i / 18 for i in BF_F[288:576]], 'o',label='BG relative change -1 h',color="Orange");
        #     plt.plot(T_F[0:288],[i / 18 for i in BGF_F[288:576]], 'o',label='Current BG relative change',color="Red");
        #     plt.plot(T_F[0:288],[i / 18 for i in GPP_F[288:576]], 'o',label='Gradient',color="Brown");
        #     plt.axhline(linewidth=2, color='Black');

        #     if flag>=0:
        #         plt.plot(peaks[0]-24,values[0]/18, 'X',label='Positive peak',color="yellow");
        #     else:
        #         plt.plot(peaks[0]-24,(-1)*values[0]/18, 'X',label='Negative peak',color="blue");    
        #     plt.grid(which='major', color='#DDDDDD', linewidth=0.8);
        #     plt.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5);

        #     plt.minorticks_on();
        #     plt.legend();
        #     # # Show the plot
        #     plt.show();
        # x=0;
        # for i in BGF_F:
        #     # print (str(x/60)+","+str(i * 18 ));
        #     x=x+5;

        # -----------------------------------------------------------#
        # Insulin arrays
        # -----------------------------------------------------------#

    # Change of insulin to recommend. Insulin_ch holds 12 values (one per 5 min)
    # for each processed hour k = 20 ... 51. h_i, h_f: hours dropped at the
    # start and end of that span.
    h_i=4;
    h_f=4;

    # Timing of the recommended change. The dose for the deviation read at
    # hour k is sized above assuming it is delivered from k-2 h to k-1 h
    # (get_insulin_type: time = peaks - 2). LEAD_HOURS places it there in the
    # recommended profile too: the day hour h receives the dose computed for
    # hour h + LEAD_HOURS. The day is repeated three times, so doses near
    # midnight wrap to the end of the same day. LEAD_HOURS is set in globals.py;
    # LEAD_HOURS = 0 reproduces the
    # earlier version, in which each dose was applied in the hour of the
    # deviation.
    # (see the Notes of the header)
    LEAD_HOURS = globals.LEAD_HOURS

    # In_int: the 288 values (24 h) of the day, taken LEAD_HOURS later in the
    # list, so that day hour h receives the change computed for hour
    # h + LEAD_HOURS. In_i and In_f are not used.
    In_i=Insulin_ch[:h_i*12]
    In_f=Insulin_ch[(k-range_i+1-h_f)*12:]
    In_int=Insulin_ch[(h_i+LEAD_HOURS)*12:(k-range_i+1-h_f+LEAD_HOURS)*12]
        # -----------------------------------------------------------#
        # Modifying final Insulin array
        # -----------------------------------------------------------#



    # for i in range(h_i*12):
    #     In_int[len(In_int)-h_i*12+i]=In_int[len(In_int)-h_i*12+i]+In_i[i]


    # for i in range(h_f*12):
    #     # print(i)      
    #     In_int[i]=In_int[i]+In_f[i]


        # -----------------------------------------------------------#
        # Saving key variables
        # -----------------------------------------------------------#


    # Key of the output: every 5 minutes, 288 times, 00:00:00 ... 23:55:00
    # (the last one generated is 00:00:00 of the next day; sort puts it first).
    dt = datetime.datetime(2010, 12, 1);
    end = datetime.datetime(2010, 12, 1, 23, 59, 59);
    step = datetime.timedelta(minutes=1);

    secArray=[];
    # -----------------------------------------------------------#;
    j=1;
    while dt < end:
            dt += step;
            if j%5==0:
                secArray.append(dt.strftime('%H:%M:%S'));
            j=j+1;
    secArray.sort()

        # -----------------------------------------------------------#
        # Saving values in a dataframe
        # -----------------------------------------------------------#

    # df: corrected guide (BGFin) and original guide (BGIni), both from the
    # middle copy of the day (slots 288-575), and the change of rate (InCh, in
    # U/h: dose per 5 min x 12).
    df = pd.DataFrame();
    df['Key']=secArray;
    df['BGFin']=BGF_F[288:576];
    df['BGIni']=np.concatenate([BG_initial,BG_initial,BG_initial[0:276]])[288:576];
    df['InCh']= [element * 12 for element in In_int] ;

        # -----------------------------------------------------------#
        # Read Basal rates
        # -----------------------------------------------------------#  
    # Join onto the table of step 13 (every minute); the minutes between the
    # 5-minute values are filled forward (and backward at the start).
    dataBasal= pd.read_csv(str(path2)+fileToRead);
    dataBasal['Key']=dataBasal['Key'].str.strip();
        # -----------------------------------------------------------#
        # Rename redundant  variables
        # -----------------------------------------------------------#
    if r>0:
        dataBasal.rename(columns = {'BGFin':'BGFin'+str(r+1)}, inplace = True);
        dataBasal.rename(columns = {'BGIni':'BGIni'+str(r+1)}, inplace = True);
        dataBasal.rename(columns = {'InCh':'InCh'+str(r+1)}, inplace = True);
        # -----------------------------------------------------------#
    df['Key']=df['Key'].str.strip();
    output1 = pd.merge(dataBasal,df,suffixes=('',''),on='Key',how='left');
        # -----------------------------------------------------------#
        # Imput values
        # -----------------------------------------------------------#
    output2=output1.replace('',float('NaN')).ffill().bfill();
        # -----------------------------------------------------------#
        # Save values
        # -----------------------------------------------------------#
    # Saved as SampledAdvised<id2>_1.csv.
    output2.to_csv(str(path2)+str(fileToSave)+"_"+str(r+1)+".csv",index=False);


datafinal= pd.read_csv(str(path2)+str(fileToSave)+"_"+str(r+1)+".csv");
        # -----------------------------------------------------------#
        # Sum of insulin changes
        # -----------------------------------------------------------#
# Total change (sum of every InCh column; one, with a single pass) and the
# recommended rate RecIns = programmed rate (BasalInfused) + change.
prefix = 'InCh';
cols_with_prefix = [col for col in datafinal.columns if col.startswith(prefix)];
datafinal[f'{prefix}_sum'] = datafinal[cols_with_prefix].sum(axis=1);
datafinal['RecIns']=datafinal[f'{prefix}_sum']+datafinal['BasalInfused'];
        # -----------------------------------------------------------#
        # Correction of negative values
        # -----------------------------------------------------------#
# Copy the original 'RecIns' values to a new column for comparison
# Recommended rate = programmed rate + change; negative rates are corrected below.
datafinal['AdjustedRecIns'] = datafinal['RecIns'];

# A rate cannot be negative. When the recommended reduction is larger than the
# rate of that minute, the rate is set to zero and the part of the reduction
# that does not fit is moved NEGATIVE_RATE_SHIFT_MIN (120, globals.py) minutes earlier (wrapping to the end of the
# day for the first 120 minutes), where it is subtracted; that rate is also
# kept at or above zero, so a reduction never becomes an increase.
for i in range(len(datafinal)):
    if datafinal.at[i, 'AdjustedRecIns'] < 0:
        excess = abs(datafinal.at[i, 'AdjustedRecIns'])
        datafinal.at[i, 'AdjustedRecIns'] = 0;
        j = i - globals.NEGATIVE_RATE_SHIFT_MIN if i >= globals.NEGATIVE_RATE_SHIFT_MIN else len(datafinal) - globals.NEGATIVE_RATE_SHIFT_MIN + i
        datafinal.at[j, 'AdjustedRecIns'] = max(0.0, datafinal.at[j, 'AdjustedRecIns'] - excess)
# InsChange: the change actually recommended, after the zero bound
# (recommended rate - programmed rate).
datafinal['InsChange']=+datafinal['AdjustedRecIns']-datafinal['BasalInfused'];


# Combine with a dummy date (or real date if you have it)
# Each hour keeps a single value: if its first 5 minutes differ from the rest
# of the hour (the forward fill above), they take the rest's value (its mode).
datafinal['Timestamp'] = pd.to_datetime("2025-01-01 " + datafinal['Key'].astype(str))

# Set it as the index
datafinal.set_index('Timestamp', inplace=True)

# Now use the fixed version
inschange = datafinal['InsChange'].copy()

# Group by full hour
for hour, group in inschange.groupby(inschange.index.floor('h')):
    first_5_idx = group[group.index.minute < 5].index
    rest = group[group.index.minute >= 5]

    if not rest.empty:
        rest_val = rest.mode().iloc[0]
        if not (group.loc[first_5_idx] == rest_val).all():
            inschange.loc[first_5_idx] = rest_val

datafinal['InsChange'] = inschange


# # 1) Extract hour from 'Key' (strings like "HH:MM:SS")
# datafinal['hour'] = pd.to_datetime(datafinal['Key'], format='%H:%M:%S').dt.hour

# # 2) Representative value per hour
# hourly = datafinal.groupby('hour')['AdjustedRecIns'].first().sort_index()

# # 3) Circular shift BACK by 1 hour:
# #    new(h) = old((h+1) % 24) so hour 23 gets hour 0's value
# shifted = hourly.shift(-1)
# shifted.iloc[-1] = hourly.iloc[0]   # fill the wrap-around correctly

# # 4) Map back
# datafinal['AdjustedRecIns'] = datafinal['hour'].map(shifted)

# # 5) Clean up
# datafinal.drop(columns='hour', inplace=True)
# -----------------------------------------------------------#
# Conversion to arrays to graph
# -----------------------------------------------------------#
# Figure (shown, not saved): programmed rate, change and recommended rate,
# every 5 minutes.
Key=[];
InsChange=[];
AdjustedRecIns=[];
BasalInfused=[];


Key=datafinal["Key"].to_numpy();
InsChange=datafinal["InsChange"].to_numpy();
AdjustedRecIns=datafinal["AdjustedRecIns"].to_numpy();
BasalInfused=datafinal["BasalInfused"].to_numpy();


T_Key=[];
T_InsChange=[];
T_AdjustedRecIns=[];
T_BasalInfused=[];


# Sampling
for i in range(len(Key)):
    # print(i);
    (h, m, s) = Key[i].split(':');
    result = (int(h) * 3600 + int(m) * 60 + int(s))/3600;
    if i % int(Sampling_time*60) ==True:
        T_Key.append(result);
        T_InsChange.append(InsChange[i]);
        T_AdjustedRecIns.append(AdjustedRecIns[i]);
        T_BasalInfused.append(BasalInfused[i]);


# Add titles and labels
plt.title('Changes in Basal Rates: '+str(id2) )
plt.xlabel('Time')
plt.ylabel('Basal Rates (U/h)')

# Plot a horizontal line at y=0 for reference
plt.axhline(linewidth=2, color='Black')


plt.plot(T_Key, T_BasalInfused, 'o--', label='Original Basal Rates', color="green")

plt.plot(T_Key, T_InsChange, 'o--', label='Changes in Basal Rates Suggested', color="blue")

plt.plot(T_Key, T_AdjustedRecIns, 'o--', label='New Basal Rates Suggested', color="Red")

# Add grid lines
plt.grid(which='major', color='#DDDDDD', linewidth=0.8)
plt.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5)

# Add a legend to differentiate the lines
plt.legend()


# Show the plot
plt.show()
# Mean recommended rate, printed as a check.
mean_value = np.mean(T_AdjustedRecIns)
print(mean_value)

# Final table SampledAdvised<id2>_final.csv, read by step 15.
datafinal.to_csv(str(path2)+str(fileToSave)+"_"+"final"+".csv",index=False);
