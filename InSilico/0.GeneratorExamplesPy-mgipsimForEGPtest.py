#Code: 0.GeneratorExamplesPy-mgipsimForEGPtest.py 
#Description: Create examples from  py-mgipsim simulator.
#Created  29th March 2025
#Author: mbaxdg6


from datetime import timedelta
from datetime import datetime
from simglucose.controller.pid_ctrller import PIDController
import csv
import pandas as pd
import os
from matplotlib import pyplot as plt
import glob
import globals
import json
import math


# -----------------------------------------------------------#
# Configuration variables
# -----------------------------------------------------------#


id=globals.id;
id2=globals.id2;


filetoread = globals.fileToSave;
# Location of patient files
path = globals.path
fileJSON=str(id2)+".json";
# Location to save Meal and bolus files
fileToSave = globals.fileToSave;
BGFile='/state_results.xlsx';


new_folder_name = f"Simulation_{id2}"
new_folder_path = os.path.join(filetoread, new_folder_name)
# -----------------------------------------------------------#
# Read Basal rates
# -----------------------------------------------------------#


file_path = os.path.join(new_folder_path, "simulation_settings.json")
# Load JSON from file
with open(file_path, 'r') as f:
    data = json.load(f)



basal_rate=data["inputs"]["basal_insulin"]["magnitude"]
basal_rate_starting_pont=data["inputs"]["basal_insulin"]["start_time"]
# Save the updated JSON back to the file
with open(file_path, 'w') as f:
    json.dump(data, f, indent=4)


# Flatten the lists of magnitudes and start times
mags = [m for sublist in basal_rate for m in sublist]  # Flatten the magnitudes
starts = [s for sublist in basal_rate_starting_pont for s in sublist]  # Flatten the start times

starts.append(1440);
# -----------------------------------------------------------#
# Validate inputs
# -----------------------------------------------------------#

if len(mags) + 1 != len(starts):
    raise ValueError("`starts` must have exactly one more element than `mags`.")

# -----------------------------------------------------------#
# Basal rates time series generation
# -----------------------------------------------------------#

total_minutes = 24 * 60  # Total duration in minutes (24 hours)
time_series = []

# Generate the per-minute time series based on rates
for i in range(len(mags)):
    start = int(starts[i])
    end = int(starts[i + 1])
    value_per_min = mags[i] / 60.0

    for minute in range(start, min(end, total_minutes)):
        time_str = f"{minute // 60:02}:{minute % 60:02}:00"
        time_series.append((time_str, value_per_min))

# -----------------------------------------------------------#
# Create DataFrame and save output
# -----------------------------------------------------------#

# Convert to DataFrame
df = pd.DataFrame(time_series, columns=["Key", "BasalValue0"])

# File naming
file_name_1 = f"{fileToSave}/BasalLeftJoined_ini_{str(id2)}.csv"
file_name_2 = f"{fileToSave}/BasalLeftJoined{str(id2)}.csv"

# Save both CSVs
df.to_csv(file_name_1, index=False)
df.to_csv(file_name_2, index=False)


print(f"Data saved to:\n  → {file_name_1}\n  → {file_name_2}")

# -----------------------------------------------------------#
# Blood Glucose
# -----------------------------------------------------------#

print(new_folder_path);

#  Load the Excel file
file_path = new_folder_path+BGFile
sheet_name = "Patient_0"  

#  Read the sheet into a DataFrame
dataBG = pd.read_excel(file_path, sheet_name=sheet_name)

dataBG.columns = dataBG.columns.str.strip().str.replace(r'[\r\n\t\u00A0]', '', regex=True)
dataBG['BGValue'] = dataBG['IG (mmol/L)'] * 18.0182
BG_values = dataBG['BGValue']


# -----------------------------------------------------------#
# Save values
# -----------------------------------------------------------#


records_per_day = 1440
total_records = len(dataBG)
num_days = math.ceil(total_records / records_per_day)


time_range = pd.date_range(start="00:00:00", end="23:59:59", freq="1min").time
key = [t.strftime("%H:%M:%S") for t in time_range] * num_days

# Trim key to match data length
key = key[:total_records]

# Assign keys and index
dataBG = dataBG.iloc[:total_records].copy()
dataBG['Key'] = key
dataBG['Index'] = dataBG.index

# Add Day column
day_labels = []
for day in range(1, num_days + 1):
    day_labels.extend([day] * min(records_per_day, total_records - len(day_labels)))
dataBG['Day'] = day_labels

# Subset
subset_columns = ["Index", "Key", "BGValue"]
subset_df = dataBG[subset_columns]

# Save to CSV
subset_df.to_csv(fileToSave + '/BGDay_ini_' + str(id2) + '.csv', index=False)


# -----------------------------------------------------------#
# Divde files
# -----------------------------------------------------------#

# Load the CSV file
file_path = fileToSave  + '/BGDay_ini_' + str(id2) + '.csv' 
df = pd.read_csv(file_path) 

# Define the chunk size
chunk_size = 1440  

# Split and save each chunk
for i, start in enumerate(range(0, len(df), chunk_size)):
    chunk = df.iloc[start:start + chunk_size]
    chunk.to_csv(fileToSave  + '/BG'+str(id2) + '_'+str(i+1) + '.csv', index=False)