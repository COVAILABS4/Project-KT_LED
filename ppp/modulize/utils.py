# utils.py

# from Constant import Constants
import json
import machine




# # Importing the necessary functions from file_operation.py
from file_operations import (
    get_data, 
    set_data, 
    update_local_json_schedule, 
    update_local_json_color, 
    update_local_json_add_rack, 
    update_local_json_click, 
    update_local_json_enabled,
    update_local_json_remove_rack,
    update_local_json_remove_schedule,
    update_local_json_schedule_enabled,
    
    # load_json_rack
)

from QueueManager import QueueManager
# from station import  Station

# sta = Station()


QObject = QueueManager()

# const = Constants()


# def handle_operation(rec_data,wlan_mac,const):
#     print(rec_data , wlan_mac , const)


# Defining handle_operation function
def handle_operation(rec_data,wlan_mac,const,bin_const):
    
    # print(wlan_mac)
    print("COMMING")
    print(rec_data)
    
    operation = rec_data.get('operation')
    
    if operation == 'add-master':
        new_group_id = rec_data.get('new_group_id')
        new_data = [{"Group_id": new_group_id, "racks": []}]
        set_data(new_data)
        const.set_current_group_id(new_group_id)
        const.set_current_rack([])
        const.set_group_index(0)
        

    
    elif operation == 'remove-master':
        new_data = [{"Group_id": "", "racks": []}]
        set_data(new_data)

        const.set_current_group_id("")
        const.set_current_rack([])
        const.set_group_index(0)

    
    elif operation == 'push':
        group_id = rec_data.get('group_id')
        rack_id = rec_data.get('rack_id')
        bin_id = rec_data.get('bin_id')
        new_schedule_time = rec_data.get('new_schedule_time')
        color = rec_data.get('color')
        
        mac, bin_idx = update_local_json_schedule(group_id, rack_id, bin_id, new_schedule_time, color)
        if mac:
            msg = {
                "operation": "push",
                "binIndex": bin_idx,
                "schedulesTime": new_schedule_time,
                "color": color
            }
            if not wlan_mac == mac:
                send_message(mac, json.dumps(msg))
    
    
    elif operation == 'color-change':
        group_id = rec_data.get('group_id')
        rack_id = rec_data.get('rack_id')
        bin_id = rec_data.get('bin_id')
        color = rec_data.get('color')

        
        
        mac, bin_idx = update_local_json_color(group_id, rack_id, bin_id, color,const,bin_const=bin_const)
        if mac:
            msg = {
                "operation": "color-change",
                "binIndex": bin_idx,
                "color": color
            }
            if not wlan_mac == mac:
                send_message(mac, json.dumps(msg))
    
    elif operation == 'add-rack':
        group_id = rec_data.get('group_id')
        new_rack_id = rec_data.get('new_rack_id')
        mac_str = rec_data.get('mac')
        
        master_mac, rack = update_local_json_add_rack(group_id, new_rack_id, mac_str,wlan_mac)
        if not wlan_mac == bytes(mac_str):
            msg = {
                "operation": "add-rack",
                "new_rack_id": new_rack_id,
                "master": [i for i in wlan_mac]
            }
            send_message(bytes(mac_str),  json.dumps(msg))
        else:
            # machine.reset()
            # const.
            const.set_current_rack(rack)
            # load_json_rack(data, wlan_mac)
    
    elif operation == 'click-change':
        group_id = rec_data.get('group_id')
        rack_id = rec_data.get('rack_id')
        bin_id = rec_data.get('bin_id')
        
        mac, bin_idx = update_local_json_click(group_id, rack_id, bin_id)
        const.remove_from_active_bins(rack_id, bin_idx)
        const.check_and_update_buzzer_relay()
        
        if mac:
            msg = {
                "operation": "click-change",
                "binIndex": bin_idx,
            }
            if not wlan_mac == mac:
                send_message(mac, json.dumps(msg))
            else:
                bin_const._bins[bin_idx].clicked = True

                bin_const._bins[bin_idx].turn_off_leds()
    
    elif operation == 'enable-change':
        group_id = rec_data.get('group_id')
        rack_id = rec_data.get('rack_id')
        bin_id = rec_data.get('bin_id')
        
        mac, bin_idx = update_local_json_enabled(group_id, rack_id, bin_id)
        if mac:
            msg = {
                "operation": "enable-change",
                "binIndex": bin_idx,
            }
            if not wlan_mac == mac:
                send_message(mac, json.dumps(msg))
            else:
                bin_const._bins[bin_idx].enabled = not bin_const._bins[bin_idx].enabled
                if bin_const._bins[bin_idx].enabled:
                    bin_const._bins[bin_idx].change_led_color()
                else:
                    bin_const._bins[bin_idx].turn_off_leds()
    
    elif operation == 'remove-rack':
        group_id = rec_data.get('group_id')
        rack_id = rec_data.get('rack_id')
        
        if update_local_json_remove_rack(group_id, rack_id):
            msg = {
                "operation": "remove-rack",
                "group_id": group_id,
                "rack_id": rack_id
            }
            send_message(wlan_mac, json.dumps(msg))
        else:
            print(f"Failed to remove rack {rack_id} from group {group_id}.")

            
    
    elif operation == 'remove-schedule':
        group_id = rec_data.get('group_id')
        rack_id = rec_data.get('rack_id')
        bin_id = rec_data.get('bin_id')
        scheduled_time = rec_data.get('scheduled_time')
        
        if update_local_json_remove_schedule(group_id, rack_id, bin_id, scheduled_time):
            msg = {
                "operation": "remove-schedule",
                "group_id": group_id,
                "rack_id": rack_id,
                "bin_id": bin_id,
                "scheduled_time": scheduled_time
            }
            send_message(wlan_mac, json.dumps(msg))
        else:
            print(f"Failed to remove schedule index {scheduled_time} from bin {bin_id}.")
    
    elif operation == 'schedule-change':
        group_id = rec_data.get('group_id')
        rack_id = rec_data.get('rack_id')
        bin_id = rec_data.get('bin_id')
        scheduled_index = rec_data.get('scheduled_index')
        current_enabled_status = rec_data.get('current_enabled_status')
        
        mac, bin_idx = update_local_json_schedule_enabled(group_id, rack_id, bin_id, scheduled_index, current_enabled_status)
        if mac:
            msg = {
                "operation": "schedule-change",
                "binIndex": bin_idx,
                "scheduled_index": scheduled_index,
                "current_enabled_status": current_enabled_status
            }
            if not wlan_mac == mac:
                send_message(mac, json.dumps(msg))
            else:
                bin_const._bins[bin_idx].enabled = not bin_const._bins[bin_idx].enabled
                if bin_const._bins[bin_idx].enabled:
                    bin_const._bins[bin_idx].change_led_color()
                else:
                    bin_const._bins[bin_idx].turn_off_leds()


def send_message(mac, msg):
    print("Senting meesagess")
    # Add message to the queue
    QObject.add_message_queue([[i for i in mac], msg])
    # print(f"Message added to queue: {msg}")
