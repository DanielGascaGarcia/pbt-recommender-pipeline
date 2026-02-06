#Code: 0.GeneratorExamplesZenodo.py 
#Description: Create examples from  dataset.
#Created  29th March 2025
#Author: mbaxdg6


import csv
import os
from collections import defaultdict
from datetime import datetime
import globals
# -----------------------------------------------------------#
# Configuration variables
# -----------------------------------------------------------#

id = globals.id;

filetoread = globals.filetoread1;
fileToSave = globals.fileToSave;


os.makedirs(fileToSave, exist_ok=True)

# -----------------------------------------------------------#
# Utility function: parse datetimes flexibly
# -----------------------------------------------------------#
def parse_datetime(ts_str):
    ts_str = ts_str.strip()
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y  %H:%M:%S"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    print(f"Could not parse datetime: {ts_str}")
    return None

# -----------------------------------------------------------#
# General-purpose processor for splitting files by date
# -----------------------------------------------------------#
def process_csv_by_date(input_path, output_prefix, headers, timestamp_index, row_processor):
    data_by_date = defaultdict(list)

    if os.path.isfile(input_path):
        with open(input_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)
            print(f"[{output_prefix}] Header: {header}")

            for row in reader:
                if len(row) < len(headers):
                    continue
                dt = parse_datetime(row[timestamp_index])
                if not dt:
                    continue
                date_key = dt.strftime("%Y%m%d")
                formatted_ts = dt.strftime("%H:%M:%S")  # Only time portion
                processed_row = row_processor(formatted_ts, row)
                data_by_date[date_key].append(processed_row)

        print(f"[{output_prefix}] Total unique dates: {len(data_by_date)}")

        for date_key in sorted(data_by_date.keys()):
            filename = f"{output_prefix}{id}_{date_key}.csv"
            path = os.path.join(fileToSave, filename)
            with open(path, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data_by_date[date_key])
            print(f"[{output_prefix}] Saved: {path}")
    else:
        print(f"[{output_prefix}] File not found: {input_path}")

# -----------------------------------------------------------#
# Process Glucose
# -----------------------------------------------------------#
process_csv_by_date(
    input_path=os.path.join(filetoread, f"UoMGlucose{id}.csv"),
    output_prefix="UoMGlucose",
    headers=["Key", "BGValue"],
    timestamp_index=0,
    row_processor=lambda ts, row: [ts, row[1].strip()]
)

# -----------------------------------------------------------#
# Process Nutrition
# -----------------------------------------------------------#
process_csv_by_date(
    input_path=os.path.join(filetoread, f"UoMNutrition{id}.csv"),
    output_prefix="UoMNutrition",
    # headers=["Key", "meal_type", "meal_tag", "CHO", "prot_g", "fat_g", "fibre_g"],
    headers=["Key", "CHO"],
    timestamp_index=0,
    row_processor=lambda ts, row: [ts] + row[1:7]
)

# -----------------------------------------------------------#
# Process Bolus
# -----------------------------------------------------------#
process_csv_by_date(
    input_path=os.path.join(filetoread, f"UoMBolus{id}.csv"),
    output_prefix="UoMBolus",
    headers=["Key", "bolus_dose"],
    timestamp_index=0,
    row_processor=lambda ts, row: [ts, row[1].strip()]
)

# -----------------------------------------------------------#
# Process Basal
# -----------------------------------------------------------#
process_csv_by_date(
    input_path=os.path.join(filetoread, f"UoMBasal{id}.csv"),
    output_prefix="UoMBasal",
    headers=["Key", "basal_dose", "insulin_kind"],
    timestamp_index=0,
    row_processor=lambda ts, row: [ts, row[1].strip(), row[2].strip()]
)
