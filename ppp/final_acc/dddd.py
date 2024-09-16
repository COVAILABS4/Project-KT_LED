import json
import network
import espnow
import time
from ubinascii import hexlify
import usocket as socket
import _thread
import urequests as requests
import machine
from neopixel import NeoPixel
import ujson
from ds3231 import DS3231

e = None
# data = []
wlan_mac = None;

server_ip = ""

KIT_NO = 1

STATIC_IP = 1


SERVER_NO = 254

SSID = 'ACTFIBERNET'
PASSWORD = 'act12345'



# Define file path
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

# Read existing configuration
Local = read_config(config_file_path)

# Store configuration values in variables
KIT_NO = Local.get("KIT_NO", "")
STATIC_IP = Local.get("STATIC_NO", "")

if STATIC_IP=="":
    STATIC_IP = KIT_NO


SERVER_NO = Local.get("SERVER_NO", 0)
SSID = Local.get("SSID", "")
PASSWORD = Local.get("PASSWORD", "")


# Print variables
print("KIT_NO =", KIT_NO)
print("STATIC_NO =", STATIC_IP)
print("SERVER_NO =", SERVER_NO)
print("SSID =", SSID)
print("PASSWORD =", PASSWORD)




# Define I2C pins for SDA and SCL
sda_pin = machine.Pin(21)
scl_pin = machine.Pin(22)
# Initialize I2C
i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin)
time.sleep(0.5)  # Short delay to ensure I2C is ready

# Initialize the DS3231 RTC module
rtc = DS3231(i2c)


isAvail = False
sta = network.WLAN(network.STA_IF)
sta.active(True)


buzzer_pin = 32
relay_pin = 33
buzzer = machine.Pin(buzzer_pin, machine.Pin.OUT)
relay = machine.Pin(relay_pin, machine.Pin.OUT)

# Shared state for buzzer and relay management
active_bins = [] 

def get_data():
    data = []
    with open("data.json", 'r') as f:
        data= json.load(f)
    
    return data;


def set_data(new_data):
    # data = []
    with open('data.json', 'w') as f:
        json.dump(new_data, f)
    
    # return data;



def connect_to_wifi(ssid, password):
    """Connect to the Wi-Fi network and handle IP extraction and modification."""
    global server_ip;
    if not sta.isconnected():
        print('Connecting to network', end="")
        sta.connect(ssid, password)
        
        # Start time for the connection attempt
        start_time = time.time()
        
        while not sta.isconnected():
            print(".", end="")
            time.sleep(1)
            
            # Check if 10 seconds have passed
            if time.time() - start_time > 10:
                print("\nFailed to connect within 10 seconds.")
                check_and_reset()
                return
        
        print()
    
    print('Network configuration:', sta.ifconfig())
    
    # Extract and modify IP address
    ip_info = sta.ifconfig()
    ip_address = ip_info[0]
    
    # Split IP address into parts
    ip_parts = ip_address.split('.')
    
    # Construct new IP address
    if len(ip_parts) == 4:
        new_ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{STATIC_IP}"
        print(f"New IP address to be set: {new_ip_address}")
        

        server_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{SERVER_NO}"
        # Set new IP address (optional)
        sta.ifconfig((new_ip_address, ip_info[1], ip_info[2], ip_info[3]))
        print('Updated network configuration:', sta.ifconfig())
    else:
        print("Unexpected IP address format.")

def disconnect_wifi():
    global sta
    if sta.isconnected():
        sta.disconnect()
        print('WiFi disconnected')
def get_mac():  
    sta.active(True)
    wlan_mac = sta.config('mac')
    
    return wlan_mac

def add_to_active_bins(rack_id, bin_index, color):
    """ Add bin rack_id, index, and color to the active bins list if not already present. """
    global active_bins
    if (rack_id, bin_index) not in [(b[0], b[1]) for b in active_bins]:  # Check if (rack_id, bin_index) is not already in the list
        active_bins.append((rack_id, bin_index, color))
        print(f"Added bin {bin_index} in rack {rack_id} with color {color} to active bins.")

def remove_from_active_bins(rack_id, bin_index):
    """ Remove bin rack_id and index from the active bins list. """
    global active_bins
    active_bins = [b for b in active_bins if not (b[0] == rack_id and b[1] == bin_index)]
    print(f"Removed bin {bin_index} in rack {rack_id} from active bins.")


class Bin:
    def __init__(self, bin_config, index, rack_id):
        self.button_pin = bin_config['button_pin']
        self.led_pin = bin_config['led_pin']
        self.color = tuple(bin_config['color'])
        self.last_pressed_time = 0
        self.clicked = bin_config['clicked']
        self.enabled = bin_config['enabled']
        self.schedules = bin_config['schedules']
        self.index = index  # Store the index
        self.rack_id = rack_id

        # Initialize the button and NeoPixel strip
        self.button = machine.Pin(self.button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.num_leds = 10
        self.np = NeoPixel(machine.Pin(self.led_pin), self.num_leds)

        # Set up the button interrupt
        self.button.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.handle_button_press)
        print(f"Button configured on pin {self.button_pin}")
        
        # Initialize LEDs based on the configuration
        self.initialize_leds()

    def change_led_color(self):
        for i in range(self.num_leds):
            self.np[i] = self.color
        self.np.write()
        print(f"LEDs changed to color: {self.color}")

    def turn_off_leds(self):
        for i in range(self.num_leds):
            self.np[i] = (0, 0, 0)
        self.np.write()
        print("LEDs turned off.")

    def initialize_leds(self):
        if self.clicked:
            self.turn_off_leds()
        else:
            self.change_led_color()

    def handle_button_press(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_pressed_time) > 200:  # Debounce delay
            print(f"Button pressed for bin {self.button_pin}")
            self.last_pressed_time = current_time
            self.clicked = True # Toggle clicked state
            
            if not self.clicked:
                self.change_led_color()
                add_to_active_bins(self.rack_id, self.index, self.color)  # Add to active bins
            else:
                self.turn_off_leds()
                remove_from_active_bins(self.rack_id, self.index)  # Remove from active bins
            
            # Send button press status to master
            self.send_message(self.index, 'click-change')
            check_and_update_buzzer_relay()  # Check buzzer and relay status after button press

    def send_message(self, bin_index, operation):
        msg = ujson.dumps({
            'rack_id': self.rack_id,
            'bin_idx': bin_index,
            'operation': operation
        })
        update_data_json_from_message(msg)
        print(f"Sent message to : {msg}")

current_group_id,current_rack,group_index = None , None , None
def load_json_rack(data,mac):
    global current_group_id,current_rack,group_index;
    if not len(data[0].get('racks')):
        return
    for group in data:
        if bytes(group['racks'][0]['mac']) == mac:
            current_group_id = group['Group_id']
            current_rack = group['racks'][0]
            group_index = data.index(group)
    print("Finished")
    config_all(current_rack)

# -- BINS
bins = []



def config_all(config):
    if not config:
        return
    for i, bin_config in enumerate(config['bins']):
        bins.append(Bin(bin_config, i, config['rack_id']))
        print(f"Bin {i + 1} Configured")
    bins[0].color = (64,0,0)
    bins[0].change_led_color()
    time.sleep(0.5)

    bins[0].color = (0,64,0)
    bins[0].change_led_color()
    time.sleep(0.5)

    bins[0].color = (0,0,64)
    bins[0].change_led_color()
    time.sleep(0.5)
    bins[0].color = (0,0,0)
    bins[0].change_led_color()
    time.sleep(0.5)
    for i in bins:
        i.color = (0,0,0)
        i.change_led_color()
    print("All bins initialized and ready.")


receive_thread_soc = None

def start_server():
    global server_ip;
    s = None
    try:
        addr = socket.getaddrinfo(server_ip, 8000)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception as err:
        check_and_reset()
    try:
        try:
            s.bind(addr)
        except Exception:
            pass
        s.listen(1)
        print('Listening on', addr)
        while True:
            try:
                cl, addr = s.accept()
                print('Client connected from', addr)
                cl_file = cl.makefile('rwb', 0)
                request_line = cl_file.readline().decode('utf-8').strip()
                method, path, version = request_line.split()

                sev_data = None
                try:
                    headers = {}
                    while True:
                        line = cl_file.readline().decode('utf-8').strip()
                        if not line:
                            break
                        key, value = line.split(': ', 1)
                        headers[key] = value

                    content_length = int(headers.get('Content-Length', 0))
                    post_data = cl_file.read(content_length)
                    print('POST Data:', post_data)
                    sev_data = json.loads(post_data)
                    response = {'status': 'success'}
                    cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
                    cl.send(json.dumps(response))
                    
                except Exception as err:
                    print(f"Error handling POST request: {err}")
                    check_and_reset()
                    response = {'status': 'error', 'message': str(err)}
                    cl.send('HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n')
                    cl.send(json.dumps(response))
                finally:
                    cl.close();
                
                if sev_data is not None:
                    handle_operation(sev_data)
                
                print(cl)
            except Exception as err:
                print(f"Error processing request: {err}")
                check_and_reset()
    except Exception as err:
        print("Error binding socket:", err)
    finally:
        if s is not None:
            s.close()

def receive_message(e):
    global rtc
    while True:
        host, msg = e.recv()
        
        if msg:
            if msg == b'finish':
                return
            elif msg == b"get-time":
                # Get current time from RTC
                rtc_time = rtc.get_time()
                # Format the time to send
                response = f"{rtc_time[3]}:{rtc_time[4]}:{rtc_time[5]}".encode()
                try:
                    e.add_peer(host)
                except Exception:
                    pass
                e.send(host, response)
                continue
            print(f"Received from {hexlify(host).decode()}: {msg}")
            update_data_json_from_message(msg)
        time.sleep(1)  # Adjust sleep time as per your requirements

# Function to send messages to slave
message_queue = []  # Array to store messages

def send_message(mac, msg):
    global message_queue
    
    # Add message to the queue
    message_queue.append([[i for i in mac], msg])
    print(f"Message added to queue: {msg}")

ack_received = False 


def process_message_queue():
    global sta, e, message_queue, ack_received
    
    try:
        sta.active(False)
        sta.active(True)
    except Exception as err:
        print(err)
        sta.active(True)
    remaining_queue = []
    
    for item in message_queue:
        mac, msg = tuple(item)

        mac = bytes(mac)
        try:
            try:
                e.add_peer(mac)
            except Exception:
                pass
            e.send(mac, msg)
            print(f"Sent to {mac}: {msg}")
            time.sleep(0.5)
        except Exception as err:
            print(f"Error sending message to {mac}: {err}")
            remaining_queue.append([[i for i in mac], msg])
    
    # Update the message queue with messages that did not receive acknowledgment
    message_queue = [i for i in remaining_queue]
# Function to update local JSON data for schedule

def handle_ack_received():
    global ack_received
    ack_received = True



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
def update_local_json_color(group_id, rack_id, bin_id, color):
    # print("DDD",data)
    global current_group_id,current_rack,bins

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
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None

# Function to update local JSON data for click change
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

def update_local_json_schedule_enabled(group_id, rack_id, bin_id,scheduled_index,current_enabled_status):
    global current_group_id,current_rack,bins
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

def update_local_json_remove_schedule(group_id, rack_id, bin_id, scheduled_index):
    try:
        # Load the JSON data from the file
        data = set_data()

        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                # Remove the schedule at the specified index
                                if 0 <= scheduled_index < len(bin['schedules']):
                                    del bin['schedules'][scheduled_index]
                                    print(f"Schedule {scheduled_index} removed from bin {bin_id}.")
                                else:
                                    print(f"Invalid schedule index: {scheduled_index}")
                                    return False

        # Write the updated data back to the JSON file
        set_data(data)

        print("Local JSON updated successfully after removing the schedule.")
        return True
    except Exception as err:
        print(f"Error removing schedule from local JSON: {err}")
    return False


def update_local_json_add_rack(group_id, new_rack_id, mac):
    global wlan_mac
    
    data = get_data()
    print("WEEWEWE",wlan_mac)
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
                return group['racks'][0]['mac'], new_rack['bins']
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
        with open('data.json', 'w') as f:
            json.dump(data, f)

        print(f"Rack {rack_id} removed successfully from group {group_id}.")
        return True
    except Exception as err:
        print(f"Error removing rack from local JSON: {err}")
    return False


# Function to handle different operations
def handle_operation(rec_data):
    
    global wlan_mac,current_group_id,current_rack,group_index;
    # global ;

    data = get_data()
    print(wlan_mac)
    print("COMMING")
    print(rec_data)
    print(rec_data['operation'])
    operation = rec_data['operation']

    if operation == 'add-master':
        new_group_id = rec_data['new_group_id']
        new_data = [
                {
                "Group_id": new_group_id,
                    "racks": []      
                }
            ]
        set_data(new_data)
        current_group_id = new_group_id
        current_rack = ""
        group_index = 0
    
    elif operation == 'remove-master':
        new_data = [
                {
                "Group_id": "",
                    "racks": []      
                }
            ]
        set_data(new_data)
        current_group_id = ""
        current_rack = ""
        group_index = 0
        
        
    elif operation == 'push':
        group_id = rec_data['group_id']
        rack_id = rec_data['rack_id']
    
        bin_id = rec_data['bin_id']
        mac, bin_idx = update_local_json_schedule(group_id, rack_id, bin_id, rec_data['new_schedule_time'], rec_data['color'])
        if mac:
            msg = {
                "operation": "push",
                "binIndex": bin_idx,
                "schedulesTime": rec_data['new_schedule_time'],
                "color": rec_data['color']
            }
        if not wlan_mac == mac:
            
            send_message(mac, json.dumps(msg))
            
            
    elif operation == 'color-change':
        group_id = rec_data['group_id']
        rack_id = rec_data['rack_id']
        print("CALEDD")
        bin_id = rec_data['bin_id']
        mac, bin_idx = update_local_json_color(group_id, rack_id, bin_id, rec_data['color'])
        if mac:
            msg = {
                "operation": "color-change",
                "binIndex": bin_idx,
                "color": rec_data['color']
            }
            print(wlan_mac , mac)
            if not wlan_mac == mac:
                print("CALED3333D")
                send_message(mac, json.dumps(msg))
    elif operation == 'add-rack':
        
        group_id = rec_data['group_id']
        new_rack_id = rec_data['new_rack_id']
        mac_str = rec_data['mac']

        master_mac, bin_list = update_local_json_add_rack(group_id, new_rack_id, mac_str)
        
        if not wlan_mac == bytes(mac_str):
                msg = {
                "operation": "add-rack",
                "new_rack_id": rec_data['new_rack_id'],
                "master":[i for i in wlan_mac]
                }
                send_message(bytes(mac_str), json.dumps(msg))
        else:
            # current_rack = 
            load_json_rack(data,wlan_mac)
            
    elif operation == 'click-change':
        group_id = rec_data['group_id']
        rack_id = rec_data['rack_id']
        bin_id = rec_data['bin_id']
        mac, bin_idx = update_local_json_click(group_id, rack_id, bin_id)
        remove_from_active_bins(rack_id, bin_idx)
        check_and_update_buzzer_relay()
        if mac:
            msg = {
                "operation": "click-change",
                "binIndex": bin_idx,
            }
            
            if not wlan_mac == mac:
                send_message(mac, json.dumps(msg))
            else:
                bins[bin_idx].clicked = True
                if not bins[bin_idx].clicked:
                    bins[bin_idx].change_led_color()
                else:
                    bins[bin_idx].turn_off_leds()
    elif operation == 'enable-change':
        group_id = rec_data['group_id']
        rack_id = rec_data['rack_id']
        bin_id = rec_data['bin_id']
        mac, bin_idx = update_local_json_enabled(group_id, rack_id, bin_id)
        if mac:
            msg = {
                "operation": "enable-change",
                "binIndex": bin_idx,
            }
            
            if not wlan_mac == mac:
                send_message(mac, json.dumps(msg))
            else:
                bins[bin_idx].enabled = not bins[bin_idx].enabled
                if bins[bin_idx].enabled:
                    bins[bin_idx].change_led_color()
                else:
                    bins[bin_idx].turn_off_leds()
    elif operation == 'remove-rack':
        group_id = rec_data['group_id']
        rack_id = rec_data['rack_id']
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
        group_id = rec_data['group_id']
        rack_id = rec_data['rack_id']
        bin_id = rec_data['bin_id']
        scheduled_index = rec_data['scheduled_index']
        if update_local_json_remove_schedule(group_id, rack_id, bin_id, scheduled_index):
            msg = {
                "operation": "remove-schedule",
                "group_id": group_id,
                "rack_id": rack_id,
                "bin_id": bin_id,
                "scheduled_index": scheduled_index
            }
            send_message(wlan_mac, json.dumps(msg))
        else:
            print(f"Failed to remove schedule index {scheduled_index} from bin {bin_id}.")

    
    elif operation == 'schedule-change':
        group_id = rec_data['group_id']
        rack_id = rec_data['rack_id']
        bin_id = rec_data['bin_id']
        scheduled_index = rec_data['scheduled_index']
        current_enabled_status = rec_data['current_enabled_status']
        mac, bin_idx = update_local_json_schedule_enabled(group_id, rack_id, bin_id,scheduled_index,current_enabled_status)
        if mac:
            msg = {
                "operation": "schedule-change",
                "binIndex": bin_idx,
                "scheduled_index" : scheduled_index,
                "current_enabled_status" : current_enabled_status
            }
            
            if not wlan_mac == mac:
                send_message(mac, json.dumps(msg))
            else:
                bins[bin_idx].enabled = not bins[bin_idx].enabled
                if bins[bin_idx].enabled:
                    bins[bin_idx].change_led_color()
                else:
                    bins[bin_idx].turn_off_leds()
    

notification_queue = []


def save_queues_to_backup():
    backup_data = {
        "notify": [i for i in notification_queue],
        "mess":[i for i in message_queue] 
    }


    print(backup_data)
    with open('back.json', 'w') as f:
        json.dump(backup_data, f)   
    with open('back.json', 'r') as f:
        backupdata = json.load(f)
        print(backupdata)
    time.sleep(2)

def load_queues_from_backup():
    global message_queue, notification_queue
    try:
        with open('back.json', 'r') as f:
            backup_data = json.load(f)
            notification_queue = backup_data.get("notify", [])
            message_queue = backup_data.get("mess", [])
        time.sleep(2)
        new_data = {
            "notify": [],
            "mess":[] 
        }

        with open('back.json', 'w') as f:
            json.dump(new_data, f)  
    except Exception as err:
        print("No backup found or error loading backup:", err)


def update_data_json_from_message(msg):
    global isAvail, current_group_id,current_rack,bins,notification_queue;
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
                
                remove_from_active_bins(rack_id,bin_idx)

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
                print("Com7")
                

        elif  operation=="change-color":   
            color_arr = msg_data.get('color') 
            for group in data:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        if 0 <= bin_idx < len(rack.get('bins', [])):
                            rack['bins'][bin_idx]['color'] = color_arr
                            updated = True
                            group_id = group.get('Group_id')
                        else:
                            print(f"Error: Bin index {bin_idx} out of range")
                        break
                if updated:
                    break

        

        with open('data.json', 'w') as f:
            json.dump(data, f)


        print("Data JSON updated based on received message")

        # Add notification to queue
        notification_queue.append({
            'group_id': current_group_id,
            'rack_id': rack_id,
            'bin_idx': bin_idx,
            'operation': operation,
            'color' : color_arr
        })
        # if isAvail:
            # process_notification_queue()
    except Exception as err:
        print(f"Error updating JSON from message: {err}")


def process_notification_queue():
    global server_ip,notification_queue;
    response = None
    while notification_queue:
        notification = notification_queue.pop(0)
        print(notification)
        operation = notification.get('operation')
        print("OPER - ",operation)
        api_url = "http://"+server_ip+":5000/click/update"

        try:
            print("Start")
            response = requests.post(api_url, json=notification)
            print("Start2")
            if response.status_code == 200:
                print("Server notified successfully")
            else:
                print(f"Error notifying server: {response.status_code} - {response.text}")
        except Exception as err:
            print(f"Exception occurred while notifying server: {err}")
        finally:
            if response:
                response.close()

def loaders():
    data = get_data()
    load_json_rack(data,wlan_mac)
    data = None


wlan_mac = get_mac()

# Thread and control variables
receive_thread = None
stop_thread_flag = False
def stop_thread():
    global stop_thread_flag
    stop_thread_flag = True


def check_and_reset():
    global message_queue, notification_queue
    if not message_queue and not notification_queue:
        machine.reset()
    else:
        print("Queues are not empty, saving to backup.json.")
        save_queues_to_backup()
        machine.reset()

def init_esp_now():
    global e,receive_thread,sta
    print("Initialize the ESPNOW")

    try:
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        e = espnow.ESPNow()
        e.active(True)
    except Exception :
        check_and_reset()
    if receive_thread is not None:
        stop_thread()
        time.sleep(1)  # Give some time for the thread to stop
        receive_thread = None 
    try:
        try:
            receive_thread = _thread.start_new_thread(receive_message, (e,))
        except Exception:
            check_and_reset()
        print(_thread.stack_size())
    except Exception as err:
        print(f"Error starting thread 1: {e}")
        check_and_reset()

def push_req():
    global isAvail;
    isAvail = True
    url = "http://"+server_ip+":5000/avail"  # Replace <SERVER_IP> with the actual IP address of your server
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Successfully triggered queue processing.")
        else:
            print(f"Error: Received unexpected status code {response.status_code}")
        response.close()
    except Exception as err:
        print(f"An unexpected error occurred: {err}")

def stop_req():
    global isAvail;
    isAvail = False
    url = "http://"+server_ip+":5000/stop"  # Replace <SERVER_IP> with the actual IP address of your server
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Successfully stopped queue processing.")
        else:
            print(f"Error: Received unexpected status code {response.status_code}")
        response.close()
    except Exception as err:
        print(f"An unexpected error occurred: {err}")
        
        

# Define the pin for the switch
switch_pin = machine.Pin(2, machine.Pin.IN)

threadss = None
def sent_time():
    print("NOTICED")
    global e,rtc,sta;
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    print()

    data = get_data()
    for rack in data[0]['racks'][1:]:
        rc_mac = bytes(rack['mac'])
        rtc_time = rtc.get_time()
        time = f"{rtc_time[3]}:{rtc_time[4]}:{rtc_time[5]}:999999".encode()
        try:
            e.add_peer(rc_mac)
        except Exception:
            pass
        e.send(rc_mac, time)


def notify_slave(messing):
    global e,sta;

    data = get_data()
    
    print()
    for rack in data[0]['racks'][1:]:
        rc_mac = bytes(rack['mac'])
        try:
            e.add_peer(rc_mac)
        except Exception:
            print("Already")
        print(rc_mac,messing)
        try:
            e.send(rc_mac,messing)
        except Exception:
            print("Arises")
        time.sleep(4)
        print("Notified")

def check_switch_state():
    global SSID, PASSWORD, threadss, switch_pin, e,sta
    prev_state = switch_pin.value()
    isFirst = True
    offline_toggled = False

    def AP_MODE():
        def setup_access_point():
            ap = network.WLAN(network.AP_IF)
            ap.active(True)
            ap.config(essid='ESP32-AP', password='12345678', channel=1, authmode=network.AUTH_WPA_WPA2_PSK)
            while not ap.active():
                time.sleep(1)
            print('AP Mode configured:', ap.ifconfig())
        setup_access_point()

        # Load configuration from file
        def load_config():
            try:
                with open('config.json', 'r') as f:
                    return json.load(f)
            except:
                return {"KIT_NO": "", "STATIC_NO": "", "SERVER_NO": "", "SSID": "", "PASSWORD": ""}

        # Save configuration to file
        def save_config(config):
            with open('config.json', 'w') as f:
                json.dump(config, f)
        
        # Replace placeholders in HTML with actual config values
        def render_html(template, config):
            for key, value in config.items():
                template = template.replace('{{' + key + '}}', value)
            return template
        # HTTP response handler
        def handle_request(client, config):
            request = client.recv(1024).decode('utf-8')
            if 'POST /update' in request:
                body = request.split('\r\n\r\n')[1]
                params = {k: v for k, v in [param.split('=') for param in body.split('&')]}
                config.update(params)
                save_config(config)
                response = 'HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n'
                client.send(response.encode('utf-8'))
            else:
                with open('index.txt', 'r') as f:
                    html = f.read()
                response = render_html(html, config)
                client.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'.encode('utf-8'))
                client.send(response.encode('utf-8'))

        # Start web server
        # def start_server():
        #     config = load_config()
        #     addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        #     s = socket.socket()
        #     s.bind(addr)
        #     s.listen(1)
        #     print('Web server running on http://0.0.0.0:80')

        #     while True:
        #         client, addr = s.accept()
        #         print('Client connected from', addr)
        #         handle_request(client, config)
        #         client.close()
        def start_server_AP():
            config = load_config()
            addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]  # Bind to all available network interfaces on port 8000

            try:
                s_ap = socket.socket()
                # s_ap.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:

                    s_ap.bind(addr)
                except Exception:
                    pass
                s_ap.listen(5)  # Start listening for incoming connections
                print('Web server running on http://0.0.0.0')
            except OSError as err:
                print("Socket error:", err)
                return

            while True:
                try:
                    client, addr = s_ap.accept()
                    print('Client connected from', addr)
                    print("SSSSSSSSSSS-2")
                    handle_request(client, config)
                    print("SSSSSSSSSSS-3")
                    client.close()
                except OSError as err:
                    print("Error while handling client:", err)

                print("SDSD")
        start_server_AP()
    
    while True:
        curr_state = switch_pin.value()

        if curr_state != prev_state or isFirst:
            isFirst = False
            if curr_state == 0:
            # Set up access point
    
                  # Switch ON state
                AP_MODE() 
                #_thread.start_new_thread(AP_MODE, ())
            else:  # Switch OFF state
                print("Switch OFF - Initial State")
                offline_toggled = False  # Reset toggle when the switch is first turned off
                prev_state = curr_state
                continue
            prev_state = curr_state

        elif curr_state == 1:  # Switch OFF state; handle toggling every 30 seconds
            if offline_toggled:  # Perform online state
                notify_slave("unavail")
                time.sleep(2)
                print("Switch OFF - Online State")
                connect_to_wifi(SSID, PASSWORD)
                time.sleep(2)

                if threadss is not None:
                    threadss = None

                time.sleep(2)
                try:  
                    threadss = _thread.start_new_thread(start_server, ())
                except Exception:
                    check_and_reset()

                print(f"Thread started: {threadss}")
                time.sleep(2)
                push_req()

                time.sleep(2)
                process_notification_queue()

                offline_toggled = False  

            else: 
                print("Switch OFF - Offline State")
                stop_req()
                time.sleep(2)
                disconnect_wifi()
                print("Switch OFF")
                time.sleep(2)
                init_esp_now()
                time.sleep(2)
                process_message_queue()
                time.sleep(2)
                sent_time();
                time.sleep(2)
                notify_slave("avail")

                offline_toggled = True  # Toggle back to online for next cycle

        time.sleep(50 if curr_state == 1 else 0.1)



def check_and_update_buzzer_relay():
    """ Check the state of all bins and control buzzer and relay accordingly. """
    global active_bins, buzzer, relay

    print(active_bins)


    if active_bins:
        buzzer.on()
        relay.on()
        print("Buzzer and Relay turned ON")
    else:
        buzzer.off()
        relay.off()
        print("Buzzer and Relay turned OFF")

def schedule_checker():
    print("Called")
    global  rtc, bins,current_rack
    while True:
        data = get_data()
        if not data:
            return 
        current_time = rtc.get_time()

        current_hour = str(current_time[3]) # Ensure hour and minute are two digits
        current_minute = str(current_time[4])
        
        current_hour = "0" + current_hour if len(current_hour) == 1 else current_hour
        current_minute = "0" + current_minute if len(current_minute) == 1 else current_minute
    
        print(f"Current Time: {current_hour}:{current_minute}")

        for group in data:  # Iterate through each group in the data
            for rack in group['racks']:  # Iterate through each rack in the group
                rack_id = rack['rack_id']
                for index, bin in enumerate(rack['bins']):  # Iterate through each bin in the rack
                    for schedule in bin['schedules']:
                        hour, minute = schedule['time'].split(":")
                        if schedule['enabled'] and hour == current_hour and minute == current_minute:
                            if current_rack['rack_id'] == rack_id:
                                bins[index].color = tuple(schedule['color'])
                                bins[index].change_led_color()
                                bin['clicked'] = False
                            add_to_active_bins(rack_id, index, bins[index].color)  # Store active bins in a global list
        
        check_and_update_buzzer_relay()  # Check and update the buzzer and relay status based on active bins
        time.sleep(60)  # Check every minute


loaders()

load_queues_from_backup()





# # Load configuration from file
# def load_config():
#     try:
#         with open('config.json', 'r') as f:
#             return json.load(f)
#     except:
#         return {"KIT_NO": "", "STATIC_NO": "", "SERVER_NO": "", "SSID": "", "PASSWORD": ""}

# # Save configuration to file
# def save_config(config):
#     with open('config.json', 'w') as f:
#         json.dump(config, f)

# # Replace placeholders in HTML with actual config values
# def render_html(template, config):
#     for key, value in config.items():
#         template = template.replace('{{' + key + '}}', value)
#     return template

# # HTTP response handler
# def handle_request(client, config):
#     receive = client.recv(1024).decode('utf-8')
#     print("Request:", receive)
    
#     if 'Dalvik/2.1.0 (Linux; U; Android 12; RMX2170 Build/SKQ1.210216.001)' in receive:
#         return

#       # Debug: Print the received request
#     if 'POST /update' in receive:
#         body = receive.split('\r\n\r\n')[1]
#         params = {k: v for k, v in [param.split('=') for param in body.split('&')]}
#         config.update(params)
#         save_config(config)
#         response = 'HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n'
#         client.send(response.encode('utf-8'))
#     else:
#         try:
#             with open('index.txt', 'r') as f:
#                 html = f.read()
#             response = render_html(html, config)
#             client.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'.encode('utf-8'))
#             client.send(response.encode('utf-8'))
#         except Exception as err:
#             print(f"Error handling request: {err}")
#             client.send('HTTP/1.1 500 Internal Server Error\r\n\r\n'.encode('utf-8'))


# def start_server_AP():
#     config = load_config()
#     addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]  # Bind to all available network interfaces on port 8000

#     try:
#         s_ap = socket.socket()
#         s_ap.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         s_ap.bind(addr)
#         s_ap.listen(5)  # Start listening for incoming connections
#         print('Web server running on http://0.0.0.0')
#     except OSError as err:
#         print("Socket error:", err)
#         check_and_reset()
#         return

#     while True:
#         try:
#             client, addr = s_ap.accept()
#             print('Client connected from', addr)
#             print("SSSSSSSSSSS-2")
#             handle_request(client, config)
#             print("SSSSSSSSSSS-3")
#             client.close()
#         except OSError as err:
#             print("Error while handling client:", err)

#         print("SDSD")
    
#     print("Server stopped")
    



#_thread.start_new_thread(schedule_checker, ())
check_switch_state()








