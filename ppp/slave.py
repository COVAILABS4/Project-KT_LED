import machine
import time
from neopixel import NeoPixel
import ujson
import network
import espnow
import _thread

global_time = "00:00:00"
bins = []
message_queue = []  # Initialize the queue for messages
avail = True 
received_flag = False
# Initialize RTC
rtc = machine.RTC()

def display_time():
    global rtc
    #while True:
    current_time = rtc.datetime()
    print("Current time: {:02}:{:02}:{:02}".format(current_time[4], current_time[5], current_time[6]))
    #time.sleep(120)

def send_request():
    global received_flag
    while not received_flag:
        peer = bytes(master_mac)
        try:
            e.add_peer(peer)
        except Exception:
            pass
        e.send(peer, b"get-time")  # Specify peer MAC address
        print("Sent request for time")
        time.sleep(1)
    
def init_espnow():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.disconnect()
    print("WiFi and ESP-NOW initialized.")
    
    e = espnow.ESPNow()
    e.active(True)
    return e

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

def read_schedule():
    print("Reading JSON schedule...")
    try:
        with open('sch.json', 'r') as file:
            schedule = ujson.load(file)
        print("Schedule read successfully.")
        return schedule
    except Exception as err:
        print("Failed to read schedule:", err)
        raise err

def enqueue_color_message(bin_index,color):
    global avail,rack_id
    msg = ujson.dumps({
        'rack_id': rack_id,
        'bin_idx': bin_index,
        'operation': "change-color",
        'color': color
    })
    
    message_queue.append((master_mac, msg))
#     if avail:
#         send_messages_from_queue()
    print(f"Message enqueued: {msg}")
        
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
        self.num_leds = 5
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
        global config
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_pressed_time) > 200:  # Debounce delay
            print(f"Button pressed for bin {self.button_pin}")
            self.last_pressed_time = current_time
            self.clicked = True
            if not self.clicked:
                self.change_led_color()
            else:
                self.turn_off_leds()
            config['bins'][self.index]['clicked'] = self.clicked
            with open('slave.json', 'w') as f:
                ujson.dump(config, f)
            self.enqueue_message(self.index, 'change-click')

    def enqueue_message(self, bin_index, operation):
        global avail
        msg = ujson.dumps({
            'rack_id': self.rack_id,
            'bin_idx': bin_index,
            'operation': operation
        })
        message_queue.append((self.master_mac, msg))
        print(message_queue,avail)
#         if avail:
#             send_messages_from_queue()
        print(f"Message enqueued: {msg}")


# Function to read the JSON data from the file
def read_schedule_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return ujson.load(file)
    except Exception:
        # If the file doesn't exist, return an empty structure
        return {}

# Function to write the JSON data to the file
def write_schedule_data(file_path, schedule_data):
    with open(file_path, 'w') as file:
        ujson.dump(schedule_data, file)

def change_enabled_state(file_path, index, schedule_time, current_enabled_state):
    schedule_data = read_schedule_data(file_path)
    
    # print(schedule_data)
    hour = schedule_time.split(":")[0]
    minute = schedule_time.split(":")[1]
    minute_tens = str(int(minute) // 10)

    print(schedule_data[hour][minute_tens])
    if hour in schedule_data and minute_tens in schedule_data[hour]:
        for schedule in schedule_data[hour][minute_tens]:
            if schedule["index"] == index and schedule["scheduleTime"] == schedule_time:
                schedule["enabled"] = not current_enabled_state
                write_schedule_data(file_path, schedule_data)
                return schedule_data
    return "Not Found"

# Function to add a schedule
def add_schedule(file_path, index, schedule_time, color, enabled):
    schedule_data = read_schedule_data(file_path)
    hour = schedule_time.split(":")[0]
    minute = schedule_time.split(":")[1]
    minute_tens = str(int(minute) // 10)

    if hour not in schedule_data:
        schedule_data[hour] = {str(i): [] for i in range(6)}
    
    if minute_tens not in schedule_data[hour]:
        schedule_data[hour][minute_tens] = []
    
    new_schedule = {
        "index": index,
        "scheduleTime": schedule_time,
        "color": color,
        "enabled": enabled
    }
    
    schedule_data[hour][minute_tens].append(new_schedule)
    write_schedule_data(file_path, schedule_data)
    return schedule_data

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

def handle_push_message(msg_data, config, rack_id):
    global bins
    bin_index = msg_data['binIndex']
    schedule_time = msg_data['schedulesTime']
    color = tuple(msg_data.get('color', (0, 0, 0)))  # Default to black if color is not provided

    # Create the new schedule entry
    new_schedule = {
        "time": schedule_time,
        "enabled": True,
        "color": color
    }

    # Find the bin with the given rack_id and bin_index
    for bin in bins:
        if bin.index == bin_index:
            # Insert the new schedule using insertion sort
            bin.schedules = insert_schedule(bin.schedules, new_schedule)

            # Write updated data back to slave.json
            config['bins'][bin_index]['schedules'] = bin.schedules
            with open('slave.json', 'w') as f:
                ujson.dump(config, f)
            print("Schedule updated and saved to file")
            
            add_schedule("sch.json", bin_index, schedule_time, color, True)

            break

def handle_color_change_message(msg_data, config, rack_id):
    global bins
    bin_index = msg_data['binIndex']
    color = tuple(msg_data['color'])
    print("CALLEDDD")
    
    for bin in bins:
        print(bin)
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

def handle_click_change_message(msg_data, config, rack_id):
    global bins
    bin_index = msg_data['binIndex']
    
    # Find the bin with the given rack_id and bin_index
    for bin in bins:
        if bin.index == bin_index:
            # Update clicked status in the Bin object
            bin.clicked = True

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

def handle_add_rack(msg_data):
    global bins
    print(msg_data)
    new_rack_id = msg_data['new_rack_id']
    print(new_rack_id)
    master = msg_data['master']
    print(new_rack_id, master[:2])
    new_rack = {
        "rack_id": new_rack_id,
        "master": master,
        "bins": []
    }
    led_pins = [12, 25, 26, 27]
    button_pins = [13, 14, 15, 16]
    bin_count = 4
    new_rack['bins'] = [
        {
            "color":[0, 0, 0],
            "led_pin": led_pins[i],
            "bin_id": f"{new_rack_id}_0{i+1}",
            "button_pin": button_pins[i],
            "enabled": True,
            "schedules": [],
            "clicked": False
        }
        for i in range(bin_count)
    ]
    
    
    print("nnnnnnnnnnnnnnnnnn")
    print(new_rack)
    with open('slave.json', 'w') as f:
        ujson.dump(new_rack, f)
        print("write Success")
    with open('sch.json', 'w') as f:
        ujson.dump({}, f)
        print("write Success2")
    time.sleep(1)
    main()

def handle_enable_change_message(msg_data, config, rack_id):
    global bins
    bin_index = msg_data['binIndex']
    
    # Find the bin with the given rack_id and bin_index
    for bin in bins:
        if bin.index == bin_index:
            # Update clicked status in the Bin object
            bin.enabled = not bin.enabled

            # Write updated clicked status back to slave.json
            config['bins'][bin_index]['enabled'] = bin.enabled
            with open('slave.json', 'w') as f:
                ujson.dump(config, f)
            print("enabled status changed and saved to file") 
            if not bin.enabled:
                bin.turn_off_leds()
            else:
                bin.change_led_color()
            break

def handle_schedule_enable_change_message(msg_data, config, rack_id):
    global bins
    bin_index = msg_data['binIndex']
    scheduled_index = msg_data["scheduled_index"]
    current_enabled_status = msg_data["current_enabled_status"]

    config['bins'][bin_index]['schedules'][scheduled_index]['enabled'] = not current_enabled_status
    with open('slave.json', 'w') as f:
        ujson.dump(config, f)
    change_enabled_state("sch.json", bin_index, config['bins'][bin_index]['schedules'][scheduled_index]['time'], current_enabled_status)
    print("schedule enabled status changed and saved to file") 

def espnow_listener(config, rack_id):
    global e, bins, message_queue, avail,rtc,global_time
    print("F1")
    while True:
        try:
            if e is None:
                print("ESP-NOW instance not initialized.")
                time.sleep(1)
                continue

            host, msg = e.recv()
            if msg:
                print(f"Received message from {host}: {msg}")
                if not print("F2") and  msg == b'avail':
                    avail = True
                    send_messages_from_queue()
                    continue
                    
                elif not print("F3") and  msg == b'unavail':
                    avail = False
                    print("Availability set to False")
                    continue
                elif  not print("F4") and  "999999" in msg :
                    print("Received message from peer:", msg)
                    global_time = msg.decode()
                    hour, minute, second , dummy = map(int, global_time.split(":"))
                    rtc.datetime((2024, 8, 3, 6, hour, minute, second, 0))
                    continue
                try:
                    print("F4")
                    msg_data = ujson.loads(msg)
                    operation = msg_data.get('operation')
                    print("F5")
                    if not print("F6") and  operation == 'push':
                        handle_push_message(msg_data, config, rack_id)
                        
                    elif operation == 'color-change':
                        handle_color_change_message(msg_data, config, rack_id)
                    elif operation == 'click-change':
                        handle_click_change_message(msg_data, config, rack_id)
                    elif operation == 'enable-change':
                        handle_enable_change_message(msg_data, config, rack_id)
                    elif operation == 'schedule-change':
                        handle_schedule_enable_change_message(msg_data, config, rack_id)
                    elif operation == 'add-rack':
                        handle_add_rack(msg_data)
                    else:
                        print(f"Unknown operation: {operation}")
                    
                    try:
                        e.add_peer(host)
                    except Exception:
                        print("Already added.")
                except Exception as err:
                    print(f"Unexpected error processing message: {msg}. Error: {err}")
            else:
                print("No message received.")

        except Exception as err:
            print(f"Error receiving message: {err}")
            # If the error is related to ESP-NOW instance, consider reinitializing it.
            e = init_espnow()
            try:
                e.add_peer(master_mac)
            except Exception:
                print("Already added.")

        time.sleep(1)  # Minimal delay to keep the system running

def send_messages_from_queue():
    global message_queue, e ,master_mac
    #print(message_queue)
    time.sleep(5)
    while message_queue:
        master_mac, msg = message_queue.pop(0)
        print(master_mac, msg)
        try:
            e.add_peer(bytes(master_mac))
        except Exception:
            print("Already added.")
        e.send(bytes(master_mac), msg)
        print(f"Sent message from queue to {master_mac}: {msg}")
    e.send(bytes(master_mac),"finish".encode())
config, master_mac, rack_id, e = None, None, None, None

def main():
    global config, master_mac, rack_id, e, bins, message_queue
    global rtc,global_time
    config = read_config()
    master_mac = config['master']
    rack_id = config['rack_id']

    e = init_espnow()


    try:
        e.add_peer(master_mac)
    except Exception:
        print("Already added.")
    
    
    _thread.start_new_thread(espnow_listener, (config, rack_id))
   
    bins = [Bin(bin_config, i, rack_id, e, master_mac) for i, bin_config in enumerate(config['bins'])]



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
    
    
    hour, minute, second = map(int, global_time.split(":"))
    rtc.datetime((2024, 8, 3, 6, hour, minute, second, 0))
    time.sleep(2)
    schedule_checker()
    

def update_time_from_peer():
    global global_time, received_flag
    _thread.start_new_thread(send_request, ())
    
    while not received_flag:
        host, msg = e.recv()
        
        if msg:
            print("Received message from peer:", msg)
            global_time = msg.decode()
            received_flag = True
            hour, minute, second , dummy = map(int, global_time.split(":"))
            rtc.datetime((2024, 8, 3, 6, hour, minute, second, 0))
            return
        else:
            print("No response received, retrying...")

def schedule_checker():
    print("Called")
    global bins , rtc
    schedule = read_schedule()
    while True:
        schedule = read_schedule()
        print("Called")
        current_time = rtc.datetime()
        print(current_time)
        current_hour = current_time[4]
        current_minute = current_time[5]
        day_schedule = schedule.get(str(current_hour), {})
        
        for bin_index, bin_schedule in day_schedule.items():
            print(bin_index,"-", bin_schedule)
            for entry in bin_schedule:
                print(entry['scheduleTime'],"{:02}:{:02}".format(current_hour, current_minute))
                if  entry['enabled'] and entry['scheduleTime'] == "{:02}:{:02}".format(current_hour, current_minute):
                    
                    bins[entry['index']].color = tuple(entry['color'])
                    bins[entry['index']].change_led_color()
                    bins[entry['index']].clicked = False
                    #enqueue_color_message(entry['index'],entry['color'])
        time.sleep(60)

if __name__ == "__main__":    
    main()


    

