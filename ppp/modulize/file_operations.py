# file_operations.py

import json

data_file = 'data.json'

from QueueManager import QueueManager

QObject = QueueManager()



def get_data():
    data = []
    with open("data.json", 'r') as f:
        data= json.load(f)
    
    return data;


def format_json(data):
    """Custom JSON formatter."""
    json_string = json.dumps(data)  # Convert the data to a JSON string
    formatted_json = ''
    indent_level = 0

    for char in json_string:
        if char == '{' or char == '[':
            formatted_json += char + '\n' + ' ' * (indent_level + 2)  # Add new line and custom indent
            indent_level += 2
        elif char == '}' or char == ']':
            indent_level -= 2
            formatted_json += '\n' + ' ' * indent_level + char  # Add new line and adjust indent
        elif char == ',':
            formatted_json += char + '\n' + ' ' * indent_level  # Add new line after commas
        else:
            formatted_json += char  # Append other characters as they are

    return formatted_json

def set_data(new_data):
    """Save formatted JSON to a file."""
    formatted_json = format_json(new_data)  # Format the JSON data
    with open('data.json', 'w') as f:
        f.write(formatted_json)  # Write the formatted JSON string to the file


def insert_schedule(schedules, new_schedule):
    # Convert the time strings to tuples of (hour, minute) for comparison
    new_time = tuple(map(int, new_schedule['time'].split(":")))

    inserted = False
    for i in range(len(schedules)):
        existing_time = tuple(map(int, schedules[i]['time'].split(":")))

        # Compare the times to find the correct insertion point
        if new_time < existing_time:
            schedules.insert(i, new_schedule)  # Insert at the correct position
            inserted = True
            break

    # If not inserted, append to the end
    if not inserted:
        schedules.append(new_schedule)

    return schedules


def update_local_json_schedule(group_id, rack_id, bin_id, new_schedule_time, color):
    try:
        # Open the data.json file and load the content
        data = get_data()

        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                # Create the new schedule entry
                                new_schedule = {
                                    "enabled": True,
                                    "time": new_schedule_time,
                                    "color": color
                                }

                                # Insert the new schedule using insertion sort
                                bin['schedules'] = insert_schedule(bin['schedules'], new_schedule)

                                # Write the updated data back to the JSON file
                                set_data(data)

                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None



# Function to update local JSON data for color change
def update_local_json_color(group_id, rack_id, bin_id, color,const,bin_const):
    # print("DDD",data)
    current_group_id = const.get_current_group_id
    current_rack = const.get_current_rack
    bins = bin_const._bins
    
    data = get_data()
    try:
        for group in data:
            print("DDD1")
            if group['Group_id'] == group_id:
                print("DDD5")
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        print("DD7")
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                curr_index = rack['bins'].index(bin)
                                bin['color'] = color
                                set_data(data)
                                if group_id==current_group_id and rack_id==current_rack['rack_id']:   
                                    bins[curr_index].color = color
                                    bins[curr_index].change_led_color()
                                    bin_const.set_bins(bins)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None

def update_local_json_add_rack(group_id, new_rack_id, mac,wlan_mac):
    # global wlan_mac
    
    data = get_data()
    # print("WEEWEWE",wlan_mac)
    try:
        for group in data:
            if group['Group_id'] == group_id:
                if any(rack['rack_id'] == new_rack_id for rack in group['racks']):
                    print("Rack already exists")
                    return None, None

                new_rack = {
                    "rack_id": new_rack_id,
                    "mac": mac,
                    "bins": []
                }

                if len(group['racks'])!=0 and wlan_mac != bytes(mac):
                    new_rack['master'] = group['racks'][0]['mac']

                led_pins = [12, 25, 26, 27]
                button_pins = [13, 14, 15, 16]
                bin_count = 4

                new_rack['bins'] = [
                    {
                        "color": [0,0,0],
                        "led_pin": led_pins[i],
                        "bin_id": f"{new_rack_id}_0{i+1}",
                        "button_pin": button_pins[i],
                        "enabled": True,
                        "schedules": [],
                        "clicked": False

                    }
                    for i in range(bin_count)
                ]
                
                print(wlan_mac, mac)
                if wlan_mac == bytes(mac):
                    group['racks'] = []
                
                group['racks'].append(new_rack)

                set_data(data)
                
                print(group['racks'][0]['mac'])
                print("Local JSON updated successfully with new rack")
                return group['racks'][0]['mac'], new_rack
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None


def update_local_json_click(group_id, rack_id, bin_id):

    data = get_data()
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin['clicked'] = True
                                set_data(data)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None


def update_local_json_enabled(group_id, rack_id, bin_id):
    data = get_data()
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin['enabled'] = not bin['enabled']
                                set_data(data)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None



def update_local_json_remove_rack(group_id, rack_id):

    data = get_data()
    try:

        for group in data:
            if group['Group_id'] == group_id:
                # Find and remove the rack with the given rack_id
                group['racks'] = [rack for rack in group['racks'] if rack['rack_id'] != rack_id]

        # Write the updated data back to the JSON file
        set_data(data)

        print(f"Rack {rack_id} removed successfully from group {group_id}.")
        return True
    except Exception as err:
        print(f"Error removing rack from local JSON: {err}")
    return False


def update_local_json_remove_schedule(group_id, rack_id, bin_id, schedule_time):
    try:
        # Load the JSON data from the file
        data = get_data()

        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                # Find the schedule with the matching time and get its index
                                schedule_index = -1
                                
                                for idx, schedule in enumerate(bin['schedules']):
                                    if schedule['time'] == schedule_time:
                                        schedule_index = idx
                                        break
                                
                                # Remove the schedule by index if found
                                if schedule_index != -1:
                                    del bin['schedules'][schedule_index]
                                    print(f"Schedule at {schedule_time} removed from bin {bin_id}.")
                                else:
                                    print(f"No schedule found at time: {schedule_time}")
                                    return False

        # Write the updated data back to the JSON file
        set_data(data)

        print("Local JSON updated successfully after removing the schedule.")
        return True
    except Exception as err:
        print(f"Error removing schedule from local JSON: {err}")
        return False


def update_local_json_schedule_enabled(group_id, rack_id, bin_id,scheduled_index,current_enabled_status):

    data = get_data()
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin['schedules'][scheduled_index]['enabled'] = not current_enabled_status
                                set_data(data)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None

# const = 
def update_data_json_from_message(msg,const,bin_const):
    
    

    current_group_id = const._current_group_id
    current_rack = const._current_rack
    bins = bin_const._bins

    print(current_group_id,current_rack,bins)
    data = get_data()
    try:
        msg_data = json.loads(msg)
        rack_id = msg_data.get('rack_id')
        bin_idx = msg_data.get('bin_idx')
        operation = msg_data.get('operation')
        print(rack_id, bin_idx)
        
        if not rack_id or bin_idx is None:
            print("Error: Missing required fields in the message")
            return

        updated = False
        group_id = None
        curr_state = False
        color_arr = [1,1,1]
        if operation=="change-click":
            print("Com1")
            for group in data:
                print("Com2")
                for rack in group['racks']:
                    print("Com3")
                    if rack['rack_id'] == rack_id:
                        print("Com4")
                        if 0 <= bin_idx < len(rack.get('bins', [])):
                            print("Com5")
                            rack['bins'][bin_idx]['clicked'] = True
                            curr_state = rack['bins'][bin_idx]['clicked']
                            updated = True
                            group_id = group['Group_id']
                        else:
                            print(f"Error: Bin index {bin_idx} out of range")
                        break
                
                const.remove_from_active_bins(rack_id,bin_idx)

                print(group_id,"---",rack_id,"---",bin_idx)
                # if updated:
                #     break
                print("Com6")
                if group_id == current_group_id and rack_id == current_rack['rack_id']:
                    bins[bin_idx].clicked = curr_state
                    if not bins[bin_idx].clicked:
                        bins[bin_idx].change_led_color()
                    else:
                        bins[bin_idx].turn_off_leds()
                    bin_const.set_bins(bins)
                print("Com7")
                
        set_data(data)


        print("Data JSON updated based on received message")

        # Add notification to queue
        QObject.add_notify_queue({
            'group_id': current_group_id,
            'rack_id': rack_id,
            'bin_idx': bin_idx,
            'operation': operation,
            'color' : color_arr
        })
      
    except Exception as err:
        print(f"Error updating JSON from message: {err}")
