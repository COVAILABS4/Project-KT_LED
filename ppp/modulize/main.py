#main.py

from station import Station
from Constant import Constants
import _thread

from Bin_Constant  import Bin_Constants

from Bin import Bin

from esp_now import ESPNowManager


from file_operations import get_data
import time

import ujson

from schedule import schedule_checker

import machine

import gc

gc.enable()

bin_const = Bin_Constants()

  
config_file_path = '/config.json'
def read_config(file_path):
    """Reads JSON configuration from the specified file."""
    try:
        with open(file_path, 'r') as file:
            config = ujson.load(file)
            return config
    except OSError:
        # If file does not exist, return an empty dictionary
        return {}
    
Local = read_config(config_file_path)
# Store configuration values in variables
KIT_NO = Local.get("KIT_NO", "")
STATIC_NO = Local.get("STATIC_NO", "")

if STATIC_NO=="":
    STATIC_IP = KIT_NO

SERVER_NO = Local.get("SERVER_NO", 0)
SSID = Local.get("SSID", "")
PASSWORD = Local.get("PASSWORD", "")

const = Constants()

def config_all(config):
    if not config:
        return
    for i, bin_config in enumerate(config['bins']):
        bin_const._bins.append(Bin(bin_config, i, config['rack_id'],const))
        #print(f"Bin {i + 1} Configured")
    bin_const._bins[0].color = (64,0,0)
    bin_const._bins[0].change_led_color()
    time.sleep(0.5)

    bin_const._bins[0].color = (0,64,0)
    bin_const._bins[0].change_led_color()
    time.sleep(0.5)

    bin_const._bins[0].color = (0,0,64)
    bin_const._bins[0].change_led_color()
    time.sleep(0.5)
    bin_const._bins[0].color = (0,0,0)
    bin_const._bins[0].change_led_color()
    time.sleep(0.5)


    for i in bin_const._bins:
        i.color = (0,0,0)
        i.change_led_color()
    print("All bins initialized and ready.")


def load_json_rack(data,mac):
    global const
    if not len(data[0].get('racks')):
        return
    print(mac)
    for group in data:
        if bytes(group['racks'][0]['mac']) == mac:
            const._current_group_id = group['Group_id']
            const._current_rack = group['racks'][0]
    

    print(const._current_group_id)
    print(const._current_rack)
    # print(const._current_group_id)
    print("Finished")
    
    config_all(const._current_rack)

def loaders():
    data = get_data()

    print(sta.wlan_mac,"WLAN- MAC")
    load_json_rack(data,sta.wlan_mac)
    data = None

sta = Station(ssid=SSID,password=PASSWORD,server_no=SERVER_NO,static_ip=STATIC_NO,const=const,bin_const=bin_const)

sta.set_wlan_mac()

enm = ESPNowManager(const=const,bin_const=bin_const)


loaders()






# _thread.start_new_thread(schedule_checker,(const,bin_const))

def start_sta_mode():
    offline_toggled = True
    while True:
        gc.collect()
        if offline_toggled:  # Perform online state
            
            try:
                enm.notify_slave("unavail")
            except Exception:
                pass
            time.sleep(2)
            print("Switch OFF - Online State")

            sta.connect_to_wifi()

            time.sleep(2)

            try:  
               sta.start_server() 
            except Exception:
                machine.reset()
            
            time.sleep(2)


            sta.process_notification_queue()


            
            
        else: 
            print("Switch OFF - Offline State")


            sta.stop_req()

            time.sleep(2)

            sta.disconnect_wifi()



            print("Switch OFF")
            time.sleep(2)

            enm.init_esp_now()

            time.sleep(2)

            enm.process_message_queue()

            time.sleep(2)

            enm.sent_time()


            time.sleep(4)


            enm.notify_slave("avail")

            
            time.sleep(20)

            enm.close_esp_now()
        
        offline_toggled = not offline_toggled  
        time.sleep(2)

start_sta_mode();










