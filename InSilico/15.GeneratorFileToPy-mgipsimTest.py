#Code: 14.Simulation3.py
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
import globals
import json
# -----------------------------------------------------------#
#File to read
# -----------------------------------------------------------#
# --- Configurable global variable ---
id=globals.id;
print(id)
id2=globals.id2;
print(id2)

pathRead=globals.fileToSave
pathWrite='C:/OhioDataset/ExploratoryAnalysisData/OhioT1DM/2018/parsedTexts/ZenodoData/Simulation_'+str(id2);
fileToRead="SampledAdvised"+str(id2)+"_"+"final"+".csv";   
num_days = 1  # Number of simulation days


columns_to_read = ['Key', 'AdjustedRecIns']
data = pd.read_csv(os.path.join(pathRead, fileToRead), usecols=columns_to_read)
data['AdjustedRecIns'] = data['AdjustedRecIns'] 

print(data)

# -----------------------------------------------------------#
# Load JSON and extract existing data
# -----------------------------------------------------------#
json_file_name = os.path.join(pathWrite, 'simulation_settings.json')

with open(json_file_name, 'r') as json_file:
    existing_data = json.load(json_file)

# -----------------------------------------------------------#
# Build single-day basal profile
# -----------------------------------------------------------#
magnitudes = []
start_times = []

current_rate = data.iloc[0]["AdjustedRecIns"]
current_start_time = data.iloc[0]["Key"]

for i in range(1, len(data)):
    if data.iloc[i]["AdjustedRecIns"] != current_rate:
        hh, mm, ss = map(int, current_start_time.split(":"))
        total_minutes = hh * 60 + mm + ss / 60.0
        magnitudes.append(current_rate)
        start_times.append(total_minutes)

        current_rate = data.iloc[i]["AdjustedRecIns"]
        current_start_time = data.iloc[i]["Key"]

# Handle final entry
hh, mm, ss = map(int, current_start_time.split(":"))
total_minutes = hh * 60 + mm + ss / 60.0
magnitudes.append(current_rate)
start_times.append(total_minutes)

# -----------------------------------------------------------#
# Repeat for multiple days
# -----------------------------------------------------------#
repeated_magnitudes = []
repeated_start_times = []

for day in range(num_days):
    offset = day * 1440  # offset in minutes (1 day = 1440 min)
    repeated_magnitudes.extend(magnitudes)
    repeated_start_times.extend([t + offset for t in start_times])

# -----------------------------------------------------------#
# Update JSON and save
# -----------------------------------------------------------#
existing_data["inputs"]["basal_insulin"]["magnitude"] = [repeated_magnitudes]
existing_data["inputs"]["basal_insulin"]["start_time"] = [repeated_start_times]

with open(json_file_name, 'w') as json_file:
    json.dump(existing_data, json_file, indent=4)

print("✅ Basal insulin profile updated for", num_days, "days.")