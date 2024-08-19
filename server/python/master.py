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
SSID = 'AB7'
PASSWORD = '07070707'

# Connect to WiFi
def connect_to_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(ssid, password)
    print('Connecting to WiFi...', end='')

    while not sta.isconnected():
        time.sleep(1)
    print('Connected to WiFi:', sta.ifconfig())

connect_to_wifi(SSID, PASSWORD)

# Initialize ESP-NOW
e = espnow.ESPNow()
e.active(True)

# Load JSON data from file
def load_json_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as err:
        print("Error loading JSON data:", err)
        raise

wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)

wlan_mac = wlan_sta.config('mac')
print("MAC Address:", wlan_mac)
current_group_id,current_rack,group_index = None,None,None


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
        if self.enabled:
            self.change_led_color()
            print(f"LEDs initialized with color: {self.color}")
        if self.clicked:
            self.turn_off_leds()

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

def update_data_json_from_message(msg):
    try:
        msg_data = json.loads(msg)
        rack_id = msg_data.get('rack_id')
        bin_idx = msg_data.get('bin_idx')

        if not rack_id or bin_idx is None:
            print("Error: Missing required fields in the message")
            return

        updated = False
        group_id = None

        for group in data:
            for rack in group.get('racks', []):
                if rack.get('rack_id') == rack_id:
                    if 0 <= bin_idx < len(rack.get('bins', [])):
                        rack['bins'][bin_idx]['clicked'] = True
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
        load_json_rack(data,wlan_mac)  
        print("Data JSON updated based on received message")

        api_url = 'http://192.168.231.83:5000/click/update'
        response = requests.post(api_url, json={
            'group_id': group_id,
            'rack_id': rack_id,
            'bin_idx': bin_idx
        })
        
        if response.status_code == 200:
            print("Server notified successfully")
        else:
            print(f"Error notifying server: {response.status_code} - {response.text}")

    except Exception as err:
        print(f"Error updating JSON from message: {err}")



def config_all(config):
    bins = []
    for i, bin_config in enumerate(config['bins']):
        bins.append(Bin(bin_config, i, config['rack_id']))
        print(f"Bin {i + 1} Configured")
        time.sleep(0.5)  # Add delay to ensure hardware is properly configured
    print("All bins initialized and ready.")


def load_json_rack(data,mac):
    global current_group_id,current_rack,group_index;
    for group in data:
        if bytes(group['racks'][0]['mac']) == mac:
            current_group_id = group['Group_id']
            current_rack = group['racks'][0]
            group_index = data.index(group)
    config_all(current_rack)
data = load_json_data('data.json')
load_json_rack(data,wlan_mac)
# print(current_rack)

print("Coming")
# Function to add peers from JSON data
def add_peers_from_json(data):
    for group in data:
        for rack in group['racks']:
            mac = bytes(rack['mac'])
            e.add_peer(mac)  
            print(f"Added peer: {mac}")

add_peers_from_json(data)

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
                                if group_id==current_group_id and rack_id==current_rack['rack_id']:   
                                    load_json_rack(data,wlan_mac)
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
                                bin['color'] = color
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)
                                if group_id==current_group_id and rack_id==current_rack['rack_id']:   
                                    load_json_rack(data,wlan_mac)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None

# Function to update local JSON data for click change
def update_local_json_click(group_id, rack_id, bin_id):
    print("Clicked Click")
    print(group_id, rack_id, bin_id)
    print
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin['clicked'] = not bin['clicked']
                                if group_id==current_group_id and rack_id==current_rack['rack_id']:   
                                    load_json_rack(data,wlan_mac)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, rack['bins'].index(bin)
    except Exception as err:
        print(f"Error updating local JSON: {err}")
    return None, None

# Function to handle different operations
def handle_operation(data):
    group_id = data['group_id']
    rack_id = data['rack_id']
    bin_id = data['bin_id']
    operation = data['operation']

    if operation == 'push':
        mac, bin_idx = update_local_json_schedule(group_id, rack_id, bin_id, data['new_schedule_time'], data['color'])
        if mac:
            msg = {
                "operation": "push",
                "binIndex": bin_idx,
                "schedulesTime": data['new_schedule_time'],
                "color": data['color']
            }
            send_message(mac, json.dumps(msg))
    elif operation == 'color-change':
        mac, bin_idx = update_local_json_color(group_id, rack_id, bin_id, data['color'])
        if mac:
            msg = {
                "operation": "color-change",
                "binIndex": bin_idx,
                "color": data['color']
            }
            send_message(mac, json.dumps(msg))
    elif operation == 'click-change':
        mac, bin_idx = update_local_json_click(group_id, rack_id, bin_id)
        if mac:
            msg = {
                "operation": "click-change",
                "binIndex": bin_idx,
            }
            send_message(mac, json.dumps(msg))

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
        data = json.loads(post_data)
        handle_operation(data)
        
        response = {'status': 'success'}
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
        cl.send(json.dumps(response))
    except Exception as err:
        print(f"Error handling POST request: {err}")
        response = {'status': 'error', 'message': str(err)}
        cl.send('HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n')
        cl.send(json.dumps(response))



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

# Start HTTP server in a new thread
_thread.start_new_thread(start_server, ())

# Start message receiving loop in the main thread
receive_message()


