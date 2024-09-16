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

server_ip = "192.168.65.83"

KIT_NO = 1

SERVER_NO = 83

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

#-----------------------set and get data------------------------#
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

#-----------------------END of data------------------------#

# File path for queues.json
QUEUE_FILE = 'queue.json'

def read_json():
    try:
        with open(QUEUE_FILE, 'r') as file:
            data = ujson.load(file)
            return data
    except Exception as e:
        print(f"Error reading {QUEUE_FILE}: {e}")
        return None

def write_json(data):
    try:
        with open(QUEUE_FILE, 'w') as file:
            ujson.dump(data, file)
    except Exception as e:
        print(f"Error writing to {QUEUE_FILE}: {e}")

def read_notify_queue():
    data = read_json()
    if data is not None:
        return data.get('notification_queue', [])
    return []

def add_notify_queue(item):
    data = read_json()
    if data is not None:
        data['notification_queue'].append(item)
        write_json(data)

def clear_notify_queue():
    data = read_json()
    if data is not None:
        data['notification_queue'] = []
        write_json(data)

def read_message_queue():
    data = read_json()
    if data is not None:
        return data.get('message_queue', [])
    return []

def add_message_queue(item):
    data = read_json()
    if data is not None:
        data['message_queue'].append(item)
        write_json(data)

def clear_message_queue():
    data = read_json()
    if data is not None:
        data['message_queue'] = []
        write_json(data)


#--------------------------------------END of QUEUE---------------------#

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
                machine.reset()
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
        new_ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{KIT_NO}"
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

def start_server():
    global server_ip
    s = None
    try:
        addr = socket.getaddrinfo("0.0.0.0", 8000)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setblocking(False)
        s.bind(addr)
        s.listen(1)
        print('Listening on', addr)

        time.sleep(2)
        push_req()
        
        start_time = time.time()  # Record the start time
        
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time >= 20:  # Stop server after 5 seconds
                print("Stopping server after 5 seconds.")
                break
            
            try:
                cl, addr = s.accept()
                print('Client connected from', addr)
                cl.setblocking(False)
                cl_file = cl.makefile('rwb', 0)
                
                # Non-blocking read of the request line
                request_line = b''
                while b'\r\n' not in request_line:
                    try:
                        request_line += cl_file.read(1)
                    except OSError as e:
                        if e.errno == 11:  # EAGAIN
                            if time.time() - start_time >= 5:
                                raise TimeoutError("Server timeout")
                            time.sleep(0.1)
                            continue
                        else:
                            raise e
                
                method, path, version = request_line.decode('utf-8').strip().split()
                
                # Read headers (non-blocking)
                headers = {}
                header_line = b''
                while b'\r\n\r\n' not in header_line:
                    try:
                        header_line += cl_file.read(1)
                    except OSError as e:
                        if e.errno == 11:  # EAGAIN
                            if time.time() - start_time >= 5:
                                raise TimeoutError("Server timeout")
                            time.sleep(0.1)
                            continue
                        else:
                            raise e
                
                for line in header_line.decode('utf-8').strip().split('\r\n'):
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        headers[key] = value
                
                content_length = int(headers.get('Content-Length', 0))
                
                # Read POST data (non-blocking)
                post_data = b''
                while len(post_data) < content_length:
                    try:
                        chunk = cl_file.read(content_length - len(post_data))
                        if chunk:
                            post_data += chunk
                    except OSError as e:
                        if e.errno == 11:  # EAGAIN
                            if time.time() - start_time >= 5:
                                raise TimeoutError("Server timeout")
                            time.sleep(0.1)
                            continue
                        else:
                            raise e
                
                print('POST Data:', post_data)
                sev_data = json.loads(post_data)
                response = {'status': 'success'}
                cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
                cl.send(json.dumps(response))
                
                cl.close()
                
                if sev_data is not None:
                    handle_operation(sev_data)
                
            except OSError as err:
                if err.errno == 11:  # EAGAIN, no client connected
                    time.sleep(0.1)  # Wait a bit before retrying
                else:
                    print(f"Error processing request: {err}")
                    machine.reset()
            except TimeoutError:
                print("Server timeout reached while processing request.")
                break
            except Exception as err:
                print(f"Error handling request: {err}")
                machine.reset()
                response = {'status': 'error', 'message': str(err)}
                try:
                    cl.send('HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n')
                    cl.send(json.dumps(response))
                except:
                    pass  # Client might be disconnected, ignore send errors
                finally:
                    try:
                        cl.close()
                    except:
                        pass
    except Exception as err:
        print("Error in server operation:", err)
    finally:
        if s is not None:
            s.close()
        print("Server has been shut down.")

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

def send_message(mac, msg):
    
    # Add message to the queue
    add_message_queue([[i for i in mac], msg])
    print(f"Message added to queue: {msg}")

def process_message_queue():
    global sta, e

    message_queue = read_message_queue()

    try:
        sta.active(False)
        sta.active(True)
    except Exception as err:
        print(err)
        sta.active(True)
    
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
    
    clear_message_queue()



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
    

def update_data_json_from_message(msg):
    global isAvail, current_group_id,current_rack,bins;

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
        add_notify_queue({
            'group_id': current_group_id,
            'rack_id': rack_id,
            'bin_idx': bin_idx,
            'operation': operation,
            'color' : color_arr
        })
      
    except Exception as err:
        print(f"Error updating JSON from message: {err}")


def process_notification_queue():
    global server_ip;
    response = None
    notification_queue = read_notify_queue()


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

    clear_notify_queue()


def loaders():
    data = get_data()
    load_json_rack(data,wlan_mac)
    data = None

SSID = 'AB7'
PASSWORD = '07070707'
wlan_mac = get_mac()


receive_thread = None
stop_thread_flag = False
def stop_thread():
    global stop_thread_flag
    stop_thread_flag = True

def init_esp_now():
    global e,receive_thread,sta
    print("Initialize the ESPNOW")

    try:
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        e = espnow.ESPNow()
        e.active(True)
    except Exception :
        machine.reset()
    if receive_thread is not None:
        stop_thread()
        time.sleep(1)  # Give some time for the thread to stop
        receive_thread = None 
    try:
        try:
            receive_thread = _thread.start_new_thread(receive_message, (e,))
        except Exception:
            machine.reset()
        print(_thread.stack_size())
    except Exception as err:
        print(f"Error starting thread 1: {e}")
        machine.reset()

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
    global SSID, PASSWORD, threadss, switch_pin, e
    prev_state = switch_pin.value()
    isFirst = True
    offline_toggled = False

    while True:
        curr_state = switch_pin.value()

        if curr_state != prev_state or isFirst:
            isFirst = False
            if curr_state == 0:  # Switch ON state
                print("Switch ON")
                
                # Handle only the online state
                if e is None:
                    init_esp_now()
                    time.sleep(2)
                    notify_slave("unavail")
                
                connect_to_wifi(SSID, PASSWORD)
                time.sleep(2)

                try:  
                    start_server()
                    # threadss = _thread.start_new_thread(start_server, ())
                except Exception:
                    machine.reset()

                # print(f"Thread started: {threadss}")
                # time.sleep(2)
                # push_req()

                # time.sleep(2)
                # process_notification_queue()

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

                try:  
                    start_server()
                except Exception:
                    machine.reset()
                
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
                time.sleep(20)




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


def set_default_color():
    pins = [12, 25, 26, 27]
    neopixels = [NeoPixel(machine.Pin(pin), 10) for pin in pins]
    for np in neopixels:
        for i in range(np.n):
            np[i] = (0, 0, 0)  # Set each LED to (0, 0, 0)
        np.write()  # Update the LEDs with the new color

set_default_color()

loaders()
                    

_thread.start_new_thread(schedule_checker, ())

check_switch_state()










