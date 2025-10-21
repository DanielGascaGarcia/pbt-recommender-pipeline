#Code: 14.SimulationBolusCHO.py
#Description: Adviser of new insluin doses.
#Created 1th May 2024
#Author: mbaxdg6
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
id=globals.id;
id2=globals.id2;

Convertion=18.02
# -----------------------------------------------------------#
#Reading variables
# -----------------------------------------------------------#
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




def extract_correction_bolus_from_file(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)
    return data["demographic_info"]["correction_bolus"]

# Example usage
path = globals.path
fileJSON=str(id2)+".json"


# -----------------------------------------------------------#
#File to read
# -----------------------------------------------------------#
CF = float(extract_correction_bolus_from_file(path+fileJSON));


path2=globals.fileToSave;
fileToSave="SampledAdvised"+str(id);   
# -----------------------------------------------------------#
#Main loop
# -----------------------------------------------------------#
for r in range(1):

# -----------------------------------------------------------#
#First cicle
# -----------------------------------------------------------#
    if r==0: 
            fileToRead="SampleJoined"+str(id)+".csv";
    else:
            fileToRead="SampledAdvised"+str(id)+"_"+str(r)+".csv";   

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
        BGRChInt=Convertion*data["BGRChInt"];
    else:
        BGRChInt=Convertion*data["BGFin"];
    # -----------------------------------------------------------#
    #Insulin to set up
    # -----------------------------------------------------------#
    ISF=CF;                                                                         #Insulin Sensitivity Factor[mmol/L*U].           
    #144                                                    
    t_start=[0];                                                                       #Time to start the simulation in hrs.
    Units=[1];                                                                         #Kind of units to graph
    Sampling_time=5/60;                                                                #Sampling time in hrs

    # -----------------------------------------------------------#
    # Insulin function
    # -----------------------------------------------------------#

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


    BGF_F=[];
    BG_initial=[];
    range_i=20 
    range_f=52
    Insulin_ch=[];
    for k  in range(range_i,range_f):
        # print(k-range_i)
        BG_MATF=[];
        t_BGRChInt=[];
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
        
        BG_MATF = np.concatenate([BG_MATF,BG_MATF,BG_MATF])
    # -----------------------------------------------------------#
    # Gradient on Insulin
    # -----------------------------------------------------------#
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
        BG_0=BG_MATF[0];


        if  BG_MATF_P[12*k]>0:
            flag=BG_MATF_P[k];
            values=[BG_MATF_P[12*k]]
            peaks=[k];
        # -----------------------------------------------------------#
        # -----------------------------------------------------------#
        # Compute insulin positive part
        # -----------------------------------------------------------#
        # -----------------------------------------------------------#    
            II_P,InsulinV_P,t_insulin_P=get_insulin_type(peaks,values);

            #Add each element
            for element in II_P:
                Insulin_ch.append(element)
        # -----------------------------------------------------------#
        # Call function positive part
        # -----------------------------------------------------------#
            I_MATF_P=get_curve(II_P,InsulinV_P,t_insulin_P);

        # -----------------------------------------------------------#
        # Call homologation
        # -----------------------------------------------------------#
            I_MATF_P,BG_MATF=homologation(I_MATF_P,BG_MATF);

        # -----------------------------------------------------------#
        # Call gradient
        # -----------------------------------------------------------#
            GI_MATF_P=gradient(I_MATF_P);

        # -----------------------------------------------------------#
        # Graph
        # -----------------------------------------------------------#
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


        
        # -----------------------------------------------------------# 
        # Plot Blood Glucose with dual units (mg/dL & mmol/L)
        # -----------------------------------------------------------#
        fig, ax1 = plt.subplots(figsize=(10,6))

        # Escala principal: mg/dL
        ax1.set_xlabel("Time (h)")
        ax1.set_ylabel("BG relative change (mg/dL)", color="black")
        ax1.set_title(f"Blood Glucose Dynamic ID={id}")

        # Curvas en mg/dL (con markers diferenciados y markevery para no saturar)
        ax1.plot(T_F[0:288], 
                np.concatenate([BG_initial, BG_initial, BG_initial[0:276]])[288:576],
                linestyle='-', marker='o', markevery=12, markersize=6,
                label='Original BG relative change', color="green")   

        ax1.plot(T_F[0:288], BF_F[288:576],
                linestyle='-', marker='x', markevery=12, markersize=6,
                label='BG relative change -1 h', color="orange") 

        ax1.plot(T_F[0:288], BGF_F[288:576],
                linestyle='-', marker='s', markevery=12, markersize=6,
                label='Current BG relative change', color="red")   # cuadrado

        ax1.plot(T_F[0:288], GPP_F[288:576],
                linestyle='-', marker='^', markevery=12, markersize=6,
                label='Gradient', color="brown")   # triángulo

        ax1.axhline(linewidth=2, color='black')

        # Picos (mg/dL)
        if flag >= 0:
            ax1.plot(peaks[0]-24, values[0], 'X', markersize=8,
                    label='Positive peak', color="yellow")
        else:
            ax1.plot(peaks[0]-24, -1*values[0], 'X', markersize=8,
                    label='Negative peak', color="blue")    

        # Escala secundaria: mmol/L
        def mgdl_to_mmol(x): return x / 18
        def mmol_to_mgdl(x): return x * 18

        ax2 = ax1.twinx()
        ax2.set_ylabel("BG relative change (mmol/L)", color="black")
        ax2.set_ylim(mgdl_to_mmol(ax1.get_ylim()[0]), mgdl_to_mmol(ax1.get_ylim()[1]))
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1f}'))

        # Grids y formato
        ax1.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax1.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5)
        ax1.minorticks_on()

        fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
        fig.tight_layout()

        plt.show()



        # -----------------------------------------------------------#
        # Insulin arrays
        # -----------------------------------------------------------#

    h_i=4;
    h_f=4;

    In_i=Insulin_ch[:h_i*12]
    In_f=Insulin_ch[(k-range_i+1-h_f)*12:]
    In_int=Insulin_ch[h_i*12:(k-range_i+1-h_f)*12]
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

    df = pd.DataFrame();
    df['Key']=secArray;
    df['BGFin']=BGF_F[288:576];
    df['BGIni']=np.concatenate([BG_initial,BG_initial,BG_initial[0:276]])[288:576];
    df['InCh']= [element * 12 for element in In_int] ;

        # -----------------------------------------------------------#
        # Read Basal rates
        # -----------------------------------------------------------#  
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
    output2.to_csv(str(path2)+str(fileToSave)+"_"+str(r+1)+".csv",index=False);


datafinal= pd.read_csv(str(path2)+str(fileToSave)+"_"+str(r+1)+".csv");
        # -----------------------------------------------------------#
        # Sum of insulin changes
        # -----------------------------------------------------------#
prefix = 'InCh';
cols_with_prefix = [col for col in datafinal.columns if col.startswith(prefix)];
datafinal[f'{prefix}_sum'] = datafinal[cols_with_prefix].sum(axis=1);
datafinal['RecIns']=datafinal[f'{prefix}_sum']+datafinal['BasalInfused'];
        # -----------------------------------------------------------#
        # Correction of negative values
        # -----------------------------------------------------------#
# Copy the original 'RecIns' values to a new column for comparison
datafinal['AdjustedRecIns'] = datafinal['RecIns'];

# Adjust the 'RecIns' values for the first 60 rows by adding negative values to the last 60 rows
for i in range(120):
    if datafinal.at[i, 'AdjustedRecIns'] < 0:
        # Add the negative value to the corresponding value in the last 60 rows
        datafinal.at[len(datafinal)-120+i, 'AdjustedRecIns'] += abs(datafinal.at[i, 'AdjustedRecIns'])
        # Set the current value to zero
        datafinal.at[i, 'AdjustedRecIns'] = 0;

# Adjust the 'RecIns' values as before, but now work on 'AdjustedRecIns' for the remaining rows
for i in range(120, len(datafinal)):
    if datafinal.at[i, 'AdjustedRecIns'] < 0:
        # Add the negative value to the value 60 minutes before
        datafinal.at[i - 120, 'AdjustedRecIns'] += abs(datafinal.at[i, 'AdjustedRecIns'])
        # Set the current value to zero
        datafinal.at[i, 'AdjustedRecIns'] = 0;
datafinal['InsChange']=+datafinal['AdjustedRecIns']-datafinal['BasalInfused'];
datafinal['InsChange']=-datafinal['InsChange'];

# Combine with a dummy date (or real date if you have it)
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

# -----------------------------------------------------------#
# Conversion to arrays to graph
# -----------------------------------------------------------#
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
plt.title('Changes in Basal Rates: '+str(id) )
plt.xlabel('Time')
plt.ylabel('Basal Rates (U/h)')

# Plot a horizontal line at y=0 for reference
plt.axhline(linewidth=2, color='Black')


# plt.plot(T_Key, T_BasalInfused, 'o--', label='Original Basal Rates', color="green")

plt.plot(T_Key, T_InsChange, 'o--', label='Changes in Basal Rates Suggested', color="blue")

# plt.plot(T_Key, T_AdjustedRecIns, 'o--', label='New Basal Rates Suggested', color="Red")

# Add grid lines
plt.grid(which='major', color='#DDDDDD', linewidth=0.8)
plt.grid(which='minor', color='#DDDDDD', linestyle=':', linewidth=0.5)

# Add a legend to differentiate the lines
plt.legend()


# Show the plot
plt.show()
mean_value = np.mean(T_AdjustedRecIns)
datafinal["BGRChInt"]=Convertion*datafinal["BGRChInt"]

datafinal.to_csv(str(path2)+str(fileToSave)+"_"+"final"+".csv",index=False);


