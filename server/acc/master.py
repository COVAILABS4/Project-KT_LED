import json
import network
import espnow
import time
import utime
from ubinascii import hexlify
import usocket as socket
import _thread
import urequests as requests
import machine
from neopixel import NeoPixel
import ujson


e = None
data = []
# Connect to WiFi
def connect_to_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(ssid, password)
    print('Connecting to WiFi...', end='')

    while not sta.isconnected():
        time.sleep(1)
    print('Connected to WiFi:', sta.ifconfig())



# Initialize ESP-NOW
def espnow_init():
    global e;
    e = None
    e = espnow.ESPNow()
    e.active(True)
    
    return e




def get_mac():
    wlan_sta = network.WLAN(network.STA_IF)
    wlan_sta.active(True)
    wlan_mac = wlan_sta.config('mac')
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
#         if self.enabled:
#             
#             print(f"LEDs initialized with color: {self.color}")


    def handle_button_press(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_pressed_time) > 200:  # Debounce delay
            print(f"Button pressed for bin {self.button_pin}")
            self.last_pressed_time = current_time
            self.clicked = not self.clicked
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
    print("All bins initialized and ready.")

def add_peers_from_json(data):
    for group in data:
        for rack in group['racks']:
            mac = bytes(rack['mac'])
            
            try:
                e.add_peer(mac)
            except Exception:
                print("Already Exist")
              
            print(f"Added peer: {mac}")

def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 8000)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)
        cl_file = cl.makefile('rwb', 0)
        
        try:
            request_line = cl_file.readline().decode('utf-8').strip()
            method, path, version = request_line.split()
        
            if method == 'POST':
                handle_post(cl_file, cl)
        except Exception as err:
            print(f"Error processing request: {err}")
            response = {'status': 'error', 'message': str(err)}
            cl.send('HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n')
            cl.send(json.dumps(response))
        
        cl.close()
# Function to receive messages from slave
def receive_message():
    while True:
        host, msg = e.recv()
        if msg:
            print(f"Received from {hexlify(host).decode()}: {msg}")
            update_data_json_from_message(msg)
        time.sleep(1)  # Adjust sleep time as per your requirements

# Function to send messages to slave
def send_message(mac, msg):
    try:
        e.send(mac, msg)
        print(f"Sent to {mac}: {msg}")
    except Exception as err:
        print(f"Error sending message to {mac}: {err}")

# Function to update local JSON data for schedule
def update_local_json_schedule(group_id, rack_id, bin_id, new_schedule_time, color):
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin['schedules'].append({"enabled": False, "time": new_schedule_time, "color": color})
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)
#                                 if group_id==current_group_id and rack_id==current_rack['rack_id']:   
#                                     load_json_rack(data,wlan_mac)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None


# Function to update local JSON data for color change
def update_local_json_color(group_id, rack_id, bin_id, color):
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
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
                                bin['clicked'] = not bin['clicked']
#                                 if group_id==current_group_id and rack_id==current_rack['rack_id']:   
#                                     load_json_rack(data,wlan_mac)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None


def update_local_json_add_rack(group_id, new_rack_id, mac):
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
                        "color": [64,64,64],
                        "led_pin": led_pins[i],
                        "bin_id": f"{new_rack_id}_0{i+1}",
                        "button_pin": button_pins[i],
                        "enabled": False,
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
        main()
        
        
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
    
        bin_id = rec_data['bin_id']
        mac, bin_idx = update_local_json_color(group_id, rack_id, bin_id, rec_data['color'])
        if mac:
            msg = {
                "operation": "color-change",
                "binIndex": bin_idx,
                "color": rec_data['color']
            }
            if not wlan_mac == mac: 
                send_message(mac, json.dumps(msg))
    elif operation == 'add-rack':
        group_id = rec_data['group_id']
        new_rack_id = rec_data['new_rack_id']
        mac_str = rec_data['mac']
        try:
            e.add_peer(bytes(mac_str))
        except Exception:
            print("Already Exist")
        master_mac, bin_list = update_local_json_add_rack(group_id, new_rack_id, mac_str)
        
        if not wlan_mac == bytes(mac_str):
                msg = {
                "operation": "add-rack",
                "new_rack_id": rec_data['new_rack_id'],
                "master":master_mac
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
                bins[bin_idx].clicked = not bins[bin_idx].clicked
                if not bins[bin_idx].clicked:
                    bins[bin_idx].change_led_color()
                else:
                    bins[bin_idx].turn_off_leds()
    
                

def handle_post(request, cl):
    
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
        handle_operation(sev_data)
        
        response = {'status': 'success'}
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
        cl.send(json.dumps(response))
    except Exception as err:
        print(f"Error handling POST request: {err}")
        response = {'status': 'error', 'message': str(err)}
        cl.send('HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n')
        cl.send(json.dumps(response))

def update_data_json_from_message(msg):
    try:
        msg_data = json.loads(msg)
        rack_id = msg_data.get('rack_id')
        bin_idx = msg_data.get('bin_idx')
        print(rack_id,bin_idx)
        if not rack_id or bin_idx is None:
            print("Error: Missing required fields in the message")
            return

        updated = False
        group_id = None
        curr_state = False
        for group in data:
            print()
            for rack in group['racks']:
                print(rack['rack_id'] , rack_id)
                if rack['rack_id'] == rack_id:
                    
                    if 0 <= bin_idx < len(rack.get('bins', [])):
                        rack['bins'][bin_idx]['clicked'] = not rack['bins'][bin_idx]['clicked']
                        curr_state = rack['bins'][bin_idx]['clicked']
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

        
        if group_id==current_group_id and rack_id==current_rack['rack_id']:
            
            bins[bin_idx].clicked = curr_state
            if not bins[bin_idx].clicked:
                bins[bin_idx].change_led_color()
            else:
                bins[bin_idx].turn_off_leds()
#         bins[bin_idx] = Bin(current_rack['bins'][bin_idx], bin_idx, current_rack['rack_id'])
        print("Data JSON updated based on received message")

        start_time = utime.ticks_ms()
        api_url = 'http://192.168.231.83:5000/click/update'
        try:
            response = None
            while utime.ticks_diff(utime.ticks_ms(), start_time) < 5000:
                response = requests.post(api_url, json={
                    'group_id': group_id,
                    'rack_id': rack_id,
                    'bin_idx': bin_idx
                })
                if response.status_code == 200:
                    print("Server notified successfully")
                    break
                else:
                    print(f"Error notifying server: {response.status_code} - {response.text}")
                    break
            else:
                print("Time limit exceeded for notifying server")
        except Exception as e:
            print(f"Exception occurred while notifying server: {e}")
        finally:
            if response:
                response.close()
    except Exception as err:
        print(f"Error updating JSON from message: {err}")


def main():
    global e,data
    e = espnow_init()
    data = load_json_data('data.json')
    
    load_json_rack(data,wlan_mac)
    add_peers_from_json(data)
 
    
    



SSID = 'AB7'
PASSWORD = '07070707'

connect_to_wifi(SSID, PASSWORD)
current_group_id,current_rack,group_index = None,None,None



wlan_mac = get_mac()

print("MAC Address:", [i for i in wlan_mac])

with open("data.json", 'r') as f:
    data= json.load(f)
print(data)

_thread.start_new_thread(start_server, ())
_thread.start_new_thread(receive_message, ())

if len(data)!=0:
    main();



