#Code: 0.GeneratorBolusExamplesPy-mgipsimForEGPMealTest.py
#Description: Create examples from  py-mgipsim simulator.
#Created 24th October 2025
#Author: mbaxdg6

from simglucose.simulation.env import T1DSimEnv
from simglucose.controller.basal_bolus_ctrller import BBController
from simglucose.sensor.cgm import CGMSensor
from simglucose.actuator.pump import InsulinPump
from simglucose.patient.t1dpatient import T1DPatient
from simglucose.simulation.scenario_gen import RandomScenario
from simglucose.simulation.scenario import CustomScenario
from simglucose.simulation.sim_engine import SimObj, sim, batch_sim
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
import numpy as np

# -----------------------------------------------------------#
# Configuration variables
# -----------------------------------------------------------#

id=globals.id;
id2=globals.id2;


filetoread = globals.fileToSave;

path = globals.path;
fileJSON=str(id)+".json";

fileToSave = globals.fileToSave;
# -----------------------------------------------------------#

days=1
multiplier=1440

# -----------------------------------------------------------#
# These meals can be changed depending of the scenario 
# -----------------------------------------------------------#

meal_magnitudes=[32,30,45,85]
time_strings = ["08:16:00","10:46:00","13:53:00","18:54:00"]

# -----------------------------------------------------------#

minutes = []
for time_str in time_strings:
    t = datetime.strptime(time_str, "%H:%M:%S")
    total_minutes = t.hour * 60 + t.minute
    minutes.append(total_minutes)

meal_times=minutes;

# -----------------------------------------------------------#
#ICR
# -----------------------------------------------------------#
def extract_carbs_ratio_from_file(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)
    return data["demographic_info"]["carb_insulin_ratio"]

# -----------------------------------------------------------#
# Change name to the folder
# -----------------------------------------------------------#

folders = [f for f in glob.glob(os.path.join(filetoread, "Simulation*")) if os.path.isdir(f)]
folders.sort(key=os.path.getctime)

latest_folder = folders[-1] if folders else None

if latest_folder:
    new_folder_name = f"Simulation_{id}"
    new_folder_path = os.path.join(filetoread, new_folder_name)

    os.rename(latest_folder, new_folder_path)
    print(f"Renamed:\n{latest_folder}\n➜\n{new_folder_path}")
else:
    print("No matching Simulation folders found.")
    new_folder_path = None

# -----------------------------------------------------------#
# Extract ICR
# -----------------------------------------------------------#

ICR = float(extract_carbs_ratio_from_file(path+fileJSON));

# -----------------------------------------------------------#
# Change the length of the simulation
# -----------------------------------------------------------#
file_path = os.path.join(new_folder_path, "simulation_settings.json")

with open(file_path, 'r') as f:
    data = json.load(f)


data["settings"]["end_time"] = days*multiplier 


with open(file_path, 'w') as f:
    json.dump(data, f, indent=4)
# -----------------------------------------------------------#
# Change the Boluses
# -----------------------------------------------------------#

file_path = os.path.join(new_folder_path, "simulation_settings.json")

with open(file_path, 'r') as f:
    data = json.load(f)

# -----------------------------------------------------------#
#                            Meals
# -----------------------------------------------------------#
data["inputs"]["meal_carb"]["magnitude"] = [meal_magnitudes]
data["inputs"]["meal_carb"]["start_time"] = [meal_times]
duration_meals=data["inputs"]["meal_carb"]["duration"]
data["inputs"]["meal_carb"]["duration"]=[[duration_meals[0][0]] * len(meal_times)]
# -----------------------------------------------------------#
#                            Boluses
# -----------------------------------------------------------#
bolus_doses=np.array(meal_magnitudes) / ICR
data["inputs"]["bolus_insulin"]["magnitude"] = [bolus_doses.tolist()]
data["inputs"]["bolus_insulin"]["start_time"] = [meal_times]
data["inputs"]["bolus_insulin"]["duration"] = [[1.0] * len(meal_times)]


with open(file_path, 'w') as f:
    json.dump(data, f, indent=4)






