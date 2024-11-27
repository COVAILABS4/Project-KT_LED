import random
import pandas as pd
from datetime import datetime, timedelta

# Constants
GROUP_ID = "STA-7"
RACK_IDS = [
    "7-R1",
    "7-R2",
    "7-R3",
    "7-R4",
    "7-R5",
    "7-R6",
    "7-R7",
    "7-R8",
    "7-R9",
]

color = "0,0,255"

# RACK_IDS = [
#     "2-R1",
#     "3-R3",
# ]
BINS_PER_RACK = 4
SCHEDULES_PER_BIN = 1  # Number of schedules for each bin
START_TIME = "17:42"  # Start time in HH:MM format


# Function to generate a time interval in minutes
def generate_random_interval():
    return random.choice([5])


# Function to convert start time string to datetime object
def get_start_datetime(start_time_str):
    return datetime.strptime(start_time_str, "%H:%M")


# Data generation
data = []
schedule_tracker = {}  # Dictionary to track schedules for each bin

start_datetime = get_start_datetime(START_TIME)

# Loop through each rack and bin to generate schedules
for rack_id in RACK_IDS:
    rack_id = str(rack_id)
    for bin_suffix in range(1, BINS_PER_RACK + 1):
        bin_id = f"{rack_id}_{bin_suffix:02}"

        # Initialize the schedule list for this bin
        schedule_tracker[bin_id] = []

        # Generate the specified number of schedules for this bin
        for _ in range(SCHEDULES_PER_BIN):
            if not schedule_tracker[bin_id]:
                scheduled_time = start_datetime
            else:
                last_time = datetime.strptime(schedule_tracker[bin_id][-1], "%H:%M")
                interval = generate_random_interval()
                scheduled_time = last_time + timedelta(minutes=interval)

            scheduled_time_str = scheduled_time.strftime("%H:%M")

            # Add the unique time to the tracker's list
            schedule_tracker[bin_id].append(scheduled_time_str)

            # Create a row dictionary with the updated column names
            row = {
                "group_id": GROUP_ID,  # Updated column name
                "rack_id": rack_id,
                "bin_id": bin_id,
                "schedule_time": scheduled_time_str,  # Updated column name
                "color": color,
                # "color": f"{random.randint(0, 255)},{random.randint(0, 255)},{random.randint(0, 255)}",
            }

            data.append(row)

# Convert to DataFrame
df = pd.DataFrame(data)

# Display the generated data
print(df)

# Optionally, save to an Excel file
df.to_excel("generated_data.xlsx", index=False)
