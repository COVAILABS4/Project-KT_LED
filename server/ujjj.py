import ujson
import time
import machine
import network
import espnow

# Define the GPIO pin for the button (change to the appropriate pin)
button_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)

# Define the debounce delay in milliseconds
debounce_delay = 200  # Adjust as necessary

# Initialize WLAN
sta = network.WLAN(network.STA_IF)
sta.active(True)

# Initialize ESP-NOW
e = espnow.ESPNow()
e.active(True)

# Initial peer MAC address (example)
peer = b'\x48\xe7\x29\xa1\x90\x2c'  # Example MAC address of the receiver's WiFi interface (slave ESP32)

# Function to add or update peer MAC address
def add_update_peer(mac):
    global peer
    print(mac)
    
    # Convert MAC address string to byte format
    mac_bytes = bytes.fromhex(mac.replace(':', ''))
    print(mac_bytes)
    if peer != mac_bytes:
        e.del_peer(peer)
        peer = mac_bytes
        e.add_peer(peer)


# Function to update the clicked status in the JSON file
def update_clicked_status(group_id, rack_id, bin_id, file_path='data.json'):
    print("File path:", file_path)
    try:
        # Read the JSON data from the file
        with open(file_path, 'r') as f1:
            print("Reading file...")
            data = ujson.load(f1)
            print("Data read from file:", data)

        # Find and update the relevant entry
        for group in data:
            if group['Group_id'] == group_id:
                for rack in group['racks']:
                    if rack['rack_id'] == rack_id:
                        for bin in rack['bins']:
                            if bin['bin_id'] == bin_id:
                                print("Before update:", bin)
                                bin['clicked'] = True
                                bin['mac'] = rack['mac']  # Store the MAC address
                                print("After update:", bin)
                                break
        
        # Write the updated JSON back to the file
        with open(file_path, 'w') as f2:
            print("Writing updated data to file...")
            ujson.dump(data, f2)
            print("Data written successfully")

        print("Changed Successfully")

        # Send the updated JSON data to the corresponding ESP32
        send_json_data(data, rack['mac'])  # Send to the updated rack MAC

    except OSError as e:
        print("Error reading or updating JSON data:", e)
    except ValueError as ve:
        print("ValueError:", ve)

# Function to send JSON data via ESP-NOW
def send_json_data(data, mac):
    try:
        add_update_peer(mac)  # Update the peer MAC address
        json_str = ujson.dumps(data)
        e.send(peer, json_str.encode('utf-8'))
        print(f"Sent: {json_str} to MAC: {peer}")
    except Exception as e:
        print(f"Failed to send JSON data: {e}")

num = 1

# Define the function to be called on button press
def clicked(pin):
    global num
    # Debounce logic: wait for the debounce delay and check the button state
    time.sleep_ms(debounce_delay)
    if pin.value() == 0:  # Check if the button is still pressed
        print("Button clicked!")

        # Example data to update
        group_id = 'GRP_001'
        rack_id = 'WR002'
        bin_id = 'WR002_04'

        num += 1

        # Update clicked status
        update_clicked_status(group_id, rack_id, bin_id)

# Attach an interrupt to the button pin
button_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=clicked)

# Main loop
while True:
    # Sleep to reduce CPU usage
    time.sleep(1)

