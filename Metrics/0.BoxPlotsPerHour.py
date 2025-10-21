import pandas as pd
import matplotlib.pyplot as plt
import os
import globals

# Full file path to the Excel file
file_path = globals.file_path;

# Extract the directory to save output files in the same location
output_dir = os.path.dirname(file_path)

# 1. Load the Excel file
df = pd.read_excel(file_path)

# 2. Generate timestamps at 1-minute intervals starting from 00:00:00
timestamps = pd.date_range(start='00:00:00', periods=len(df), freq='T').time
df['ts'] = timestamps
df['hour'] = pd.to_datetime(df['ts'], format='%H:%M:%S').dt.hour

# 3. Variables to analyze
variables = ['BG_1', 'BG_2']

# 4. Create and save boxplots by hour
for var in variables:
    plt.figure(figsize=(10, 5))
    df.boxplot(column=var, by='hour', grid=False)
    plt.title(f'{var} by Hour')
    plt.suptitle('')
    plt.xlabel('Hour of Day')
    plt.ylabel(var)
    plt.tight_layout()
    
    # Save each boxplot as PNG in the same directory
    plot_filename = os.path.join(output_dir, f"{var}_boxplot_by_hour.png")
    plt.savefig(plot_filename)
    plt.close()

# 5. Calculate hourly mean and standard deviation
mean_per_hour = df.groupby('hour')[variables].mean().rename(columns=lambda x: f'{x}_mean')
std_per_hour = df.groupby('hour')[variables].std().rename(columns=lambda x: f'{x}_std')

# 6. Combine into one DataFrame
summary_stats = pd.concat([mean_per_hour, std_per_hour], axis=1)

# 7. Save to CSV in the same directory
output_csv_path = os.path.join(output_dir, "hourly_mean_and_std.csv")
summary_stats.to_csv(output_csv_path)

print(f"Analysis complete. Results saved to:\n{output_csv_path}\nAnd boxplots saved as PNG files in the same directory.")
