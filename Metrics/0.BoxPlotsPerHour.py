#Code: 0.BoxPlotsPerHour.py
#Description: Box plots of BG per hour.
#Created 11th Oct 2025
#Author: mbaxdg6

import pandas as pd
import matplotlib.pyplot as plt
import os
import globals

# -----------------------------------------------------------#
# Configuration variables
# -----------------------------------------------------------#
file_path = globals.file_path;
output_dir = os.path.dirname(file_path)


df = pd.read_excel(file_path)
timestamps = pd.date_range(start='00:00:00', periods=len(df), freq='T').time
df['ts'] = timestamps
df['hour'] = pd.to_datetime(df['ts'], format='%H:%M:%S').dt.hour
variables = ['BG_1', 'BG_2']


for var in variables:
    plt.figure(figsize=(10, 5))
    df.boxplot(column=var, by='hour', grid=False)
    plt.title(f'{var} by Hour')
    plt.suptitle('')
    plt.xlabel('Hour of Day')
    plt.ylabel(var)
    plt.tight_layout()

    plot_filename = os.path.join(output_dir, f"{var}_boxplot_by_hour.png")
    plt.savefig(plot_filename)
    plt.close()


mean_per_hour = df.groupby('hour')[variables].mean().rename(columns=lambda x: f'{x}_mean')
std_per_hour = df.groupby('hour')[variables].std().rename(columns=lambda x: f'{x}_std')
summary_stats = pd.concat([mean_per_hour, std_per_hour], axis=1)
output_csv_path = os.path.join(output_dir, "hourly_mean_and_std.csv")
summary_stats.to_csv(output_csv_path)

print(f"Analysis complete. Results saved to:\n{output_csv_path}\nAnd boxplots saved as PNG files in the same directory.")
