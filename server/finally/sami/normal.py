import json
import network
import espnow
import time
from ubinascii import hexlify
import usocket as socket
import _thread




# Load JSON data from file
try:
    with open('data.json', 'r') as f:
        data = json.load(f)
except Exception as err:
    print("Error loading JSON data:", e)
    raise

# WiFi credentials
SSID = 'AB7'
PASSWORD = '07070707'

# Connect to WiFi
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(SSID, PASSWORD)
print('Connecting to WiFi...', end='')

# Wait for connection
while not sta.isconnected():
    time.sleep(1)
print('Connected to WiFi:', sta.ifconfig())

# Initialize ESP-NOW
e = espnow.ESPNow()
e.active(True)

# Function to extract MAC addresses from data.json and add peers
def add_peers_from_json(data):
    for group in data:
        for rack in group['racks']:
            mac = bytes(rack['mac'])
            e.add_peer(mac)
            print(f"Added peer: {mac}")

# Add peers from JSON data
add_peers_from_json(data)


# Function to send messages to slave
def send_message(mac, msg):
    global e;
    try:
        e.send(mac, msg)
        print(f"Sent to {mac}: {msg}")
    except Exception as err:
        print(f"Error sending message to {mac}: {e}")

# Function to update local JSON data for schedule
def update_local_json_schedule(group_id, rack_id, bin_id, new_schedule_time, color):
    bin_idx = -1
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin_idx = rack['bins'].index(bin)
                                bin['schedules'].append({"enabled": False, "time": new_schedule_time, "color": color})
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, bin_idx
    except Exception as err:
        print(f"Error updating local JSON: {e}")
    return None, None

# Function to update local JSON data for color change
def update_local_json_color(group_id, rack_id, bin_id, color):
    bin_idx = -1
    try:
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                bin_idx = rack['bins'].index(bin)
                                bin['color'] = color
                                with open('data.json', 'w') as f:
                                    json.dump(data, f)
                                print("Local JSON updated successfully")
                                mac = bytes(rack['mac'])
                                return mac, bin_idx
    except Exception as err:
        print(f"Error updating local JSON: {e}")
    return None, None

# Function to handle the operation
def main(group_id, rack_id, bin_id, new_schedule_time, operation, color):
    if operation == 'push':
        mac, bin_idx = update_local_json_schedule(group_id, rack_id, bin_id, new_schedule_time, color)
        if mac:
            msg = {
                "operation": "push",
                "binIndex": bin_idx,
                "schedulesTime": new_schedule_time,
                "color": color
            }
            send_message(mac, json.dumps(msg))
    elif operation == 'color-change':
        mac, bin_idx = update_local_json_color(group_id, rack_id, bin_id, color)
        if mac:
            msg = {
                "operation": "color-change",
                "binIndex": bin_idx,
                "color": color
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
        main(data['group_id'], data['rack_id'], data['bin_id'], data.get('new_schedule_time'), data['operation'], data['color'])
        
        response = {'status': 'success'}
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
        cl.send(json.dumps(response))
    except Exception as err:
        print(f"Error handling POST request: {e}")
        response = {'status': 'error', 'message': str(e)}
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
        rack_id = msg_data['rack_id']
        bin_idx = msg_data['bin_idx']
        
        for group in data:
            for rack in group['racks']:
                if rack['rack_id'] == rack_id:
                    rack['bins'][bin_idx]['clicked'] = True
                    with open('data.json', 'w') as f:
                        json.dump(data, f)
                    print("Data JSON updated based on received message")
    except Exception as err:
        print(f"Error updating JSON from message: {e}")

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
                if path == '/':
                    handle_post(cl_file, cl)
                elif path == '/color-change':
                    handle_post(cl_file, cl)
        except Exception as err:
            print(f"Error processing request: {e}")
            response = {'status': 'error', 'message': str(e)}
            cl.send('HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n')
            cl.send(json.dumps(response))
        
        cl.close()

# Start HTTP server in a new thread
_thread.start_new_thread(start_server, ())

print("hello")


receive_message()
#

