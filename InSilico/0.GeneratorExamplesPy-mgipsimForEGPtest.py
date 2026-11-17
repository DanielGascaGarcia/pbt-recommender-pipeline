"""
0.GeneratorExamplesPy-mgipsimForEGPtest.py   (header of the original file reads 0.GeneratorExamplespy-mgipsim.py)
Step 0 (InSilico): read the basal-only simulation of the virtual patient
matched to the participant and write its basal profile and glucose in the
file layout of the InVivo steps.

Created: 24 October 2022
Author:  mbaxdg6 (Daniel Gasca Garcia)

What it does
    1. Basal: reads the starting basal profile of Simulation_<id2>/
       (simulation_settings_original.json, or simulation_settings.json if
       there is no copy yet) and expands it to one value per minute, in
       U/min (rate / 60).
    2. Glucose: reads state_results.xlsx (sheet Patient_0, IG in mmol/L),
       converts it to mg/dL (x MGDL_PER_MMOL) and splits it into days of
       1,440 minutes.

Inputs
    globals.id, globals.id2, globals.fileToSave, globals.sim_dir,
    globals.MGDL_PER_MMOL
    InSilico/simulations/<id>/Simulation_<id2>/simulation_settings(_original).json
    InSilico/simulations/<id>/Simulation_<id2>/state_results.xlsx

Outputs (in processed/<id>/)
    BasalLeftJoined_ini_<id2>.csv, BasalLeftJoined<id2>.csv   Key, BasalValue0 (U/min)
    BGDay_ini_<id2>.csv                                       Index, Key, BGValue (mg/dL)
    BG<id2>_<k>.csv                                           one file per simulated day

Notes
    - Reading the _original copy keeps every run starting from the same
      profile, even after step 15 has written the recommendation into
      simulation_settings.json.
    - From here on, the in-silico chain works in mg/dL (the InVivo chain
      works in mmol/L).
    - The basal-only run lasts one day, so there is one BG<id2>_1.csv.
"""

# Imports. timedelta, datetime, csv, plt and glob are not used; kept from the
# original script.
from datetime import timedelta
from datetime import datetime
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

# --- Configurable global variable ---
# id  = real participant (its files go to processed/<id>/)
# id2 = virtual patient matched to it (Patient_5, ...), used in the file names
id=globals.id;
id2=globals.id2;

# --- Folder path setup ---
# filetoread, path and fileJSON are kept from the original; not used below.
filetoread = globals.fileToSave;
# Location of patient files
path = globals.path
fileJSON=str(id2)+".json";
# Location to save Meal and bolus files
fileToSave = globals.fileToSave;
# Name of the simulator output, joined to the simulation folder below.
BGFile='/state_results.xlsx';


# Working copy of the participant's basal-only run:
# InSilico/simulations/<id>/Simulation_<id2> (no final slash, so it can be
# joined with os.path.join and with BGFile). new_folder_name is not used.
new_folder_name = f"Simulation_{id2}"
new_folder_path = globals.sim_dir(id2, id).rstrip("/")
# -----------------------------------------------------------#
# Read Basal rates
# -----------------------------------------------------------#


# The basal profile of the basal-only simulation (the one that produced
# state_results.xlsx). Once 15.GeneratorFileToPy-mgipsimTest.py has run,
# simulation_settings.json holds the recommended profile and the starting one
# is kept in simulation_settings_original.json, so read that copy when it exists.
# This keeps every run starting from the same profile.
# Starting profile: the _original copy if step 15 has already written the recommendation.
file_path = os.path.join(new_folder_path, "simulation_settings_original.json")
if not os.path.isfile(file_path):
    file_path = os.path.join(new_folder_path, "simulation_settings.json")
# Load JSON from file
with open(file_path, 'r') as f:
    data = json.load(f)



# Py-mgipsim keeps the basal profile as steps:
#   magnitude  = rate of each step, in U/h
#   start_time = minute of the day at which each step starts
# Both are lists of lists: one inner list per simulated patient (here one).
basal_rate=data["inputs"]["basal_insulin"]["magnitude"]
basal_rate_starting_pont=data["inputs"]["basal_insulin"]["start_time"]


# Flatten the lists of magnitudes and start times
mags = [m for sublist in basal_rate for m in sublist]  # Flatten the magnitudes
starts = [s for sublist in basal_rate_starting_pont for s in sublist]  # Flatten the start times

# Close the last step at minute 1440 (end of the day): step i then lasts
# from starts[i] to starts[i+1].
starts.append(1440);
# -----------------------------------------------------------#
# Validate inputs
# -----------------------------------------------------------#

# Check: one more start than magnitudes (every step has an end).
if len(mags) + 1 != len(starts):
    raise ValueError("`starts` must have exactly one more element than `mags`.")

# -----------------------------------------------------------#
# Basal rates time series generation
# -----------------------------------------------------------#

total_minutes = 24 * 60  # Total duration in minutes (24 hours)
time_series = []

# Generate the per-minute time series based on rates
# For each step, one row per minute it covers, with the rate converted
# from U/h to U/min (/ 60). Minutes beyond 1440 are dropped.
for i in range(len(mags)):
    start = int(starts[i])
    end = int(starts[i + 1])
    value_per_min = mags[i] / 60.0

    for minute in range(start, min(end, total_minutes)):
        # Time as HH:MM:SS: the Key format used by every step of the chain.
        time_str = f"{minute // 60:02}:{minute % 60:02}:00"
        time_series.append((time_str, value_per_min))

# -----------------------------------------------------------#
# Create DataFrame and save output
# -----------------------------------------------------------#

# Convert to DataFrame
df = pd.DataFrame(time_series, columns=["Key", "BasalValue0"])

# File naming
# Two copies with the same content: BasalLeftJoined<id2>.csv is read by
# step 5 (5.FillGapsBasalTest.py); the _ini_ copy keeps the starting profile.
file_name_1 = f"{fileToSave}/BasalLeftJoined_ini_{str(id2)}.csv"
file_name_2 = f"{fileToSave}/BasalLeftJoined{str(id2)}.csv"

# Save both CSVs
df.to_csv(file_name_1, index=False)
df.to_csv(file_name_2, index=False)

# Inform user
print(f"Data saved to:\n  → {file_name_1}\n  → {file_name_2}")

# -----------------------------------------------------------#
# Blood Glucose
# -----------------------------------------------------------#

print(new_folder_path);

# # Load the Excel file
# state_results.xlsx: what the simulator wrote. Sheet Patient_0 = the only
# simulated patient.
file_path = new_folder_path+BGFile
sheet_name = "Patient_0"  

# # Read the sheet into a DataFrame
dataBG = pd.read_excel(file_path, sheet_name=sheet_name)

# Clean the column names: Excel headers can carry spaces, line breaks, tabs
# or non-breaking spaces, which would make dataBG['IG (mmol/L)'] fail.
dataBG.columns = dataBG.columns.str.strip().str.replace(r'[\r\n\t\u00A0]', '', regex=True)
# The in-silico chain works in mg/dL.
# IG = interstitial glucose (what a CGM measures), in mmol/L -> mg/dL.
dataBG['BGValue'] = dataBG['IG (mmol/L)'] * globals.MGDL_PER_MMOL
BG_values = dataBG['BGValue']


# -----------------------------------------------------------#
# Save values
# -----------------------------------------------------------#

# Assume 1 value per minute, so 1440 per day
# The simulator writes one value per minute, so one day = 1,440 rows.
# num_days rounds up, so an incomplete last day is kept.
records_per_day = 1440
total_records = len(dataBG)
num_days = math.ceil(total_records / records_per_day)

# Create time key for one day (repeated)
# Key: the 1,440 times of one day (00:00:00 ... 23:59:00), repeated once per
# day and cut to the number of rows.
time_range = pd.date_range(start="00:00:00", end="23:59:59", freq="1min").time
key = [t.strftime("%H:%M:%S") for t in time_range] * num_days

# Trim key to match data length
key = key[:total_records]

# Assign keys and index
dataBG = dataBG.iloc[:total_records].copy()
dataBG['Key'] = key
# Index: the row number (0, 1, 2, ...), kept as a column.
dataBG['Index'] = dataBG.index

# Add Day column
# Day: 1 for the first 1,440 rows, 2 for the next 1,440, ... (used only here;
# not saved).
day_labels = []
for day in range(1, num_days + 1):
    day_labels.extend([day] * min(records_per_day, total_records - len(day_labels)))
dataBG['Day'] = day_labels

# Subset
subset_columns = ["Index", "Key", "BGValue"]
subset_df = dataBG[subset_columns]

# Save to CSV
# One file with every simulated minute.
subset_df.to_csv(fileToSave + '/BGDay_ini_' + str(id2) + '.csv', index=False)


# -----------------------------------------------------------#
# Divde files
# -----------------------------------------------------------#

# Load the CSV file
# Read it back and cut it into one file per day of 1,440 rows:
# BG<id2>_1.csv, BG<id2>_2.csv, ... The basal-only run lasts one day, so
# only BG<id2>_1.csv is written.
file_path = fileToSave  + '/BGDay_ini_' + str(id2) + '.csv' 
df = pd.read_csv(file_path)  # Adjust delimiter if needed

# Define the chunk size
chunk_size = 1440  

# Split and save each chunk
for i, start in enumerate(range(0, len(df), chunk_size)):
    chunk = df.iloc[start:start + chunk_size]
    chunk.to_csv(fileToSave  + '/BG'+str(id2) + '_'+str(i+1) + '.csv', index=False)
