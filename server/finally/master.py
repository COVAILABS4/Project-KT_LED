import json
import network
import espnow
import time
from ubinascii import hexlify
import usocket as socket
import _thread
import urequests as requests

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

data = load_json_data('data.json')

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
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)
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

# Function to handle HTTP POST requests
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

# Function to receive messages from slave
def receive_message():
    while True:
        host, msg = e.recv()
        if msg:
            print(f"Received from {hexlify(host).decode()}: {msg}")
            update_data_json_from_message(msg)
        time.sleep(1)  # Adjust sleep time as per your requirements

# Function to update data.json based on the received message
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

# Function to start the HTTP server
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

# Start HTTP server in a new thread

_thread.start_new_thread(start_server, ())
_thread.start_new_thread(receive_message, ())
# Start message receiving loop in the main thread






