#schedule.py

import time

from file_operations import get_data




def schedule_checker(const,bin_const):
    
    # global  rtc, bins,current_rack
    while True:
        data = get_data()
        if not data:
            return 
        current_time = const._rtc.get_time()

        current_hour = str(current_time[3]) # Ensure hour and minute are two digits
        current_minute = str(current_time[4])
        
        current_hour = "0" + current_hour if len(current_hour) == 1 else current_hour
        current_minute = "0" + current_minute if len(current_minute) == 1 else current_minute
    
        print(f"Current Time: {current_hour}:{current_minute}")

        for group in data:  # Iterate through each group in the data
            for rack in group['racks']:  # Iterate through each rack in the group
                rack_id = rack['rack_id']
                for index, bin in enumerate(rack['bins']):  # Iterate through each bin in the rack
#                     print(index,bin)
                    for schedule in bin['schedules']:
#                         print("SSCCHH",schedule)
                        hour, minute = schedule['time'].split(":")
                        if schedule['enabled'] and hour == current_hour and minute == current_minute:
                            #print("CONST",const._current_rack['rack_id'])
                            if const._current_rack['rack_id'] == rack_id:
                                bin_const._bins[index].color = tuple(schedule['color'])
                                bin_const._bins[index].change_led_color()
                                bin['clicked'] = False
                            const.add_to_active_bins(rack_id, index, bin_const._bins[index].color)  # Store active bins in a global list

        time.sleep(60) 
