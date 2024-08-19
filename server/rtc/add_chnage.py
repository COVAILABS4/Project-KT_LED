import json

# File path for sch.json
file_path = 'sch.json'

# Function to read the JSON data from the file
def read_schedule_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception:
        # If the file doesn't exist, return an empty structure
        return {}

# Function to write the JSON data to the file
def write_schedule_data(file_path, schedule_data):
    with open(file_path, 'w') as file:
        json.dump(schedule_data, file)

# Function to add a schedule
def add_schedule(file_path, index, schedule_time, color, enabled):
    schedule_data = read_schedule_data(file_path)
    hour = schedule_time.split(":")[0]
    minute = schedule_time.split(":")[1]
    minute_tens = str(int(minute) // 10)

    if hour not in schedule_data:
        schedule_data[hour] = {str(i): [] for i in range(6)}
    
    if minute_tens not in schedule_data[hour]:
        schedule_data[hour][minute_tens] = []
    
    new_schedule = {
        "index": index,
        "scheduleTime": schedule_time,
        "color": color,
        "enabled": enabled
    }
    
    schedule_data[hour][minute_tens].append(new_schedule)
    write_schedule_data(file_path, schedule_data)
    return schedule_data

# Function to change the enabled state of a schedule
def change_enabled_state(file_path, index, schedule_time, current_enabled_state):
    schedule_data = read_schedule_data(file_path)
    hour = schedule_time.split(":")[0]
    minute = schedule_time.split(":")[1]
    minute_tens = str(int(minute) // 10)

    if hour in schedule_data and minute_tens in schedule_data[hour]:
        for schedule in schedule_data[hour][minute_tens]:
            if schedule["index"] == index and schedule["scheduleTime"] == schedule_time:
                schedule["enabled"] = current_enabled_state
                write_schedule_data(file_path, schedule_data)
                return schedule_data
    return "Not Found"

# Sample usage
# Add a schedule
# schedule_data = add_schedule(file_path, 3, "16:30", [255, 255, 0], False)
# print(json.dumps(schedule_data))

# # Change the enabled state of a schedule
# schedule_data = change_enabled_state(file_path, 3, "16:30", True)
# print(json.dumps(schedule_data))
# 
# # Add another schedule
schedule_data = add_schedule(file_path, 3, "16:45", [0, 255, 0], True)
print(json.dumps(schedule_data))
# 
# # Change the enabled state of the newly added schedule
# schedule_data = change_enabled_state(file_path, 1, "16:45", False)
# print(json.dumps(schedule_data))

