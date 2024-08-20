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
data = []
wlan_mac = None;

server_ip = "192.168.231.83"

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

def connect_to_wifi(ssid, password):
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
        print()
    print('Network configuration:', sta.ifconfig())


def disconnect_wifi():
    global sta
    if sta.isconnected():
        sta.disconnect()
        print('WiFi disconnected')
def get_mac():  
    sta.active(True)
    wlan_mac = sta.config('mac')
    
    return wlan_mac


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
            self.clicked = True
            if not self.clicked:
                self.change_led_color()
            else:
                self.turn_off_leds()
            # Send button press status to master
            self.send_message(self.index, 'click-change')

    def send_message(self, bin_index, operation):
        msg = ujson.dumps({
            'rack_id': self.rack_id,
            'bin_idx': bin_index,
            'operation': operation
        })
        update_data_json_from_message(msg)
        print(f"Sent message to : {msg}")

def load_json_data(file_path):
    try:
        with open(file_path, 'r') as f:  
            new_data= json.load(f)
            return new_data
    except Exception as err:
        print("Error loading JSON data:", err)
        raise

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
        #time.sleep(0.5)  # Add delay to ensure hardware is properly configured
    for i in bins:
        i.turn_off_leds();
    print("All bins initialized and ready.")

def add_peers_from_json(data):
    global e
    for group in data:
        for rack in group['racks']:
            mac = bytes(rack['mac'])
            
            try:
                e.add_peer(mac)
            except Exception:
                print("Already Exist")
            
            print(f"Added peer: {mac}")

receive_thread_soc = None



def handle_post(request, cl):
    sev_data = None
    try:
        headers = {}
        while True:
            line = request.readline().decode('utf-8').strip()
            if not line:
                break
            key, value = line.split(': ', 1)
            headers[key] = value

        content_length = int(headers.get('Content-Length', 0))
        post_data = request.read(content_length)
        print('POST Data:', post_data)
        sev_data = json.loads(post_data)
        response = {'status': 'success'}
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
        cl.send(json.dumps(response))
        cl.close()
        
    except Exception as err:
        print(f"Error handling POST request: {err}")
        check_and_reset()
        response = {'status': 'error', 'message': str(err)}
        cl.send('HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n')
        cl.send(json.dumps(response))
    
    if sev_data is not None:
        handle_operation(sev_data)


def start_server():
    s = None
    try:
        addr = socket.getaddrinfo('0.0.0.0', 8000)[0][-1]
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
        data = []
        with open('data.json', 'r') as f:
            data = json.load(f)

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
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)  # Use indent for readability

                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None


# Function to update local JSON data for color change
def update_local_json_color(group_id, rack_id, bin_id, color):
    print("DDD",data)
    global current_group_id,current_rack,bins
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
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)
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
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin['clicked'] = True
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None


def update_local_json_enabled(group_id, rack_id, bin_id):
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin['enabled'] = not bin['enabled']
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None

def update_local_json_schedule_enabled(group_id, rack_id, bin_id,scheduled_index,current_enabled_status):
    global current_group_id,current_rack,bins
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin['schedules'][scheduled_index]['enabled'] = not current_enabled_status
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None


def update_local_json_add_rack(group_id, new_rack_id, mac):
    global wlan_mac
    
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
                        "color": [1,1,1],
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

                with open('data.json', 'w') as f:
                    json.dump(data, f)
                
                print(group['racks'][0]['mac'])
                print("Local JSON updated successfully with new rack")
                return group['racks'][0]['mac'], new_rack['bins']
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None

# Function to handle different operations
def handle_operation(rec_data):
    
    global wlan_mac;
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
        with open('data.json', 'w') as f:
            json.dump(new_data, f)
        loaders()
        
        
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
            load_json_rack(data,wlan_mac)
            
    elif operation == 'click-change':
        group_id = rec_data['group_id']
        rack_id = rec_data['rack_id']
        bin_id = rec_data['bin_id']
        mac, bin_idx = update_local_json_click(group_id, rack_id, bin_id)
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
                            group_id = group.get('Group_id')
                        else:
                            print(f"Error: Bin index {bin_idx} out of range")
                        break
                if updated:
                    break
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

        if not updated:
            print("Error: Group, rack, or bin not found")
            return

        with open('data.json', 'w') as f:
            json.dump(data, f)


        print("Data JSON updated based on received message")

        # Add notification to queue
        notification_queue.append({
            'group_id': group_id,
            'rack_id': rack_id,
            'bin_idx': bin_idx,
            'operation': operation,
            'color' : color_arr
        })
        if isAvail:
            process_notification_queue()
    except Exception as err:
        print(f"Error updating JSON from message: {err}")


def process_notification_queue():
    
    response = None
    while notification_queue:
        notification = notification_queue.pop(0)
        print(notification)
        operation = notification.get('operation')
        print("OPER - ",operation)
        if operation=="change-click":
            api_url = "http://"+server_ip+":5000/click/update"
        elif  operation=="change-color":
            api_url = "http://"+server_ip+":5000/color/update"
        try:
            response = requests.post(api_url, json=notification)
            if response.status_code == 200:
                print("Server notified successfully")
            else:
                print(f"Error notifying server: {response.status_code} - {response.text}")
        except Exception as err:
            print(f"Exception occurred while notifying server: {e}")
        finally:
            if response:
                response.close()

def loaders():
    global data
    data = load_json_data('data.json')
    load_json_rack(data,wlan_mac)

SSID = 'AB7'
PASSWORD = '07070707'
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
    
    print()
    for rack in data[0]['racks'][1:]:
        rc_mac = bytes(rack['mac'])
        try:
            e.add_peer(rc_mac)
        except Exception:
            print("Already")
        print(rc_mac,messing)
        e.send(rc_mac,messing)
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


def get_data():
    data = []
    with open("data.json", 'r') as f:
        data= json.load(f)
    
    return data[0]['racks'][0];


def schedule_checker():
    print("Called")
    global bins, rtc , data
    while True:
        config = get_data()
        if not config:
            return 
        current_time = rtc.get_time()

        print(current_time)
        current_hour = str(current_time[3]) # Ensure hour and minute are two digits
        current_minute = str(current_time[4])

        current_hour = "0" + current_hour if len(current_hour) == 1   else current_hour;
        current_minute = "0" + current_minute if len(current_minute) == 1   else current_minute;
    
        print(current_hour + " : " + current_minute)

        for index, bin in enumerate(config['bins']):  # Corrected the variable names
            for schedule in bin['schedules']:
                hour, minute = tuple(schedule['time'].split(":"))
                if schedule['enabled'] and hour == current_hour and minute == current_minute:
                    bins[index].color = tuple(schedule['color'])
                    bins[index].change_led_color()
                    bin['clicked'] = False
        time.sleep(60)



with open("data.json", 'r') as f:
    data= json.load(f)
loaders()

load_queues_from_backup()




_thread.start_new_thread(schedule_checker, ())
check_switch_state()


        





