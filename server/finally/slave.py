import machine
import time
from neopixel import NeoPixel
import ujson
import network
import espnow
import _thread


# >>> %Run -c $EDITOR_CONTENT
# MAC Address: b',\xbc\xbb\x05;\x00'
# [44, 188, 187, 5, 59, 0]
# >>> 
# Function to initialize WiFi and ESP-NOW
def init_espnow():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.disconnect()
    print("WiFi and ESP-NOW initialized.")
    
    e = espnow.ESPNow()
    e.active(True)
    return e

# Read the JSON configuration
def read_config():
    print("Reading JSON configuration...")
    try:
        with open('slave.json', 'r') as file:
            config = ujson.load(file)
        print("Configuration read successfully.")
        return config
    except Exception as err:
        print("Failed to read configuration:", err)
        raise err

class Bin:
    def __init__(self, bin_config, index, rack_id, espnow_instance, master_mac):
        self.button_pin = bin_config['button_pin']
        self.led_pin = bin_config['led_pin']
        self.color = tuple(bin_config['color'])
        self.last_pressed_time = 0
        self.clicked = bin_config['clicked']
        self.enabled = bin_config['enabled']
        self.schedules = bin_config['schedules']
        self.index = index  # Store the index
        self.rack_id = rack_id  # Store the rack_id
        self.espnow_instance = espnow_instance
        self.master_mac = master_mac

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
        if not self.clicked: 
            self.change_led_color()
        else:
            self.turn_off_leds()
        print(f"LEDs initialized with color: {self.color}")

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
        self.espnow_instance.send(self.master_mac, msg)
        print(f"Sent message to {self.master_mac}: {msg}")

def handle_push_message(msg_data, bins, config, rack_id):
    bin_index = msg_data['binIndex']
    schedule_time = msg_data['schedulesTime']
    color = tuple(msg_data.get('color', (0, 0, 0)))  # Default to black if color is not providedFind the bin with the given rack_id and bin_index
    for bin in bins:
        if bin.index == bin_index:
            # Update schedules in the Bin object
            bin.schedules.append({
                "time": schedule_time,
                "enabled": False,
                "color": color
            })

            # Write updated data back to slave.json
            config['bins'][bin_index]['schedules'] = bin.schedules
            with open('slave.json', 'w') as f:
                ujson.dump(config, f)
            print("Schedule updated and saved to file")

            # Reconfigure LED color
            bin.color = color
            bin.change_led_color()
            break

def handle_color_change_message(msg_data, bins, config, rack_id):
    bin_index = msg_data['binIndex']
    color = tuple(msg_data['color'])
    # Find the bin with the given rack_id and bin_index
    for bin in bins:
        if bin.index == bin_index:
            # Update color in the Bin object
            bin.color = color

            # Write updated color back to slave.json
            config['bins'][bin_index]['color'] = list(color)
            with open('slave.json', 'w') as f:
                ujson.dump(config, f)
            print("Color changed and saved to file") 
            bin.change_led_color()
            break

def handle_click_change_message(msg_data, bins, config, rack_id):
    bin_index = msg_data['binIndex']
    
    # Find the bin with the given rack_id and bin_index
    for bin in bins:
        if bin.index == bin_index:
            # Update clicked status in the Bin object
            bin.clicked = not bin.clicked

            # Write updated clicked status back to slave.json
            config['bins'][bin_index]['clicked'] = bin.clicked
            with open('slave.json', 'w') as f:
                ujson.dump(config, f)
            print("Clicked status changed and saved to file") 
            if bin.clicked:
                bin.turn_off_leds()
            else:
                bin.change_led_color()
            break

def espnow_listener(e, bins, config, rack_id):
    while True:
        try:
            host, msg = e.recv()
            if msg:
                print(f"Received message from {host}")
                try:
                    msg_data = ujson.loads(msg)
                    operation = msg_data.get('operation')

                    if operation == 'push':
                        handle_push_message(msg_data, bins, config, rack_id)
                    elif operation == 'color-change':
                        handle_color_change_message(msg_data, bins, config, rack_id)
                    elif operation == 'click-change':
                        handle_click_change_message(msg_data, bins, config, rack_id)
                    else:
                        print(f"Unknown operation: {operation}")

                except Exception as err:
                    print(f"Error parsing message: {msg}. Error: {err}")
        
        except Exception as err:
            print(f"Error receiving message: {err}")

        time.sleep(1)  # Minimal delay to keep the system running

# Main script
config = read_config()
master_mac = bytes(config['master'])
rack_id = config.get('rack_id')

# Initialize ESP-NOW
e = init_espnow()

# Add master MAC address as peer
e.add_peer(master_mac)
print("Master MAC address added as peer.")

# Create Bin instances for all bins in the configuration
bins = []
for i, bin_config in enumerate(config['bins']):
    bins.append(Bin(bin_config, i, rack_id, e, master_mac))
    print(f"Bin {i + 1} Configured")  # Add delay to ensure hardware is properly configured
print("All bins initialized and ready.")

# Start ESP-NOW listener in a new thread
_thread.start_new_thread(espnow_listener, (e, bins, config, rack_id))

# Main loop to keep the script running
while True:
    time.sleep(1)



