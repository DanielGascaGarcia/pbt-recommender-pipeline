"""
15.GeneratorFileToPy-mgipsimTest.py   (header of the original file reads 14.Simulation3.py)
Step 15 (InSilico): write the recommended basal profile into the settings of
the virtual patient, ready for the "After" scenarios.

Created: 1 May 2024
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Keeps a copy of the starting settings as
       simulation_settings_original.json (only the first time).
    2. Converts AdjustedRecIns (U/h, every 5 min) into a step profile: one
       entry per change of rate, with its start time in minutes.
    3. Writes it into inputs > basal_insulin (magnitude, start_time) of
       simulation_settings.json.

Inputs
    globals.id, globals.id2, globals.fileToSave, globals.sim_dir
    processed/<id>/SampledAdvised<id2>_final.csv   (step 14)
    InSilico/simulations/<id>/Simulation_<id2>/simulation_settings.json

Outputs
    InSilico/simulations/<id>/Simulation_<id2>/simulation_settings.json           recommended profile
    InSilico/simulations/<id>/Simulation_<id2>/simulation_settings_original.json  starting profile

Notes
    - The copy is made only once, so running the step again never overwrites
      the starting profile with a recommended one.
    - num_days = 1: one simulated day per scenario.
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
# Same Simulation_<id2> folder that 0.GeneratorExamplesPy-mgipsimForEGPtest.py reads.
pathWrite=globals.sim_dir(id2, id).rstrip('/');
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

# Keep the settings with the original basal profile before writing the
# recommended one into simulation_settings.json. The copy is made only once,
# so re-running this script never overwrites it with a recommended profile.
original_copy = os.path.join(pathWrite, 'simulation_settings_original.json')
if not os.path.isfile(original_copy):
    import shutil
    shutil.copy2(json_file_name, original_copy)

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
