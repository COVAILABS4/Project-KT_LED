import machine
import time
from neopixel import NeoPixel
import ujson
import network
import espnow
import _thread 
import sys
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
    machine.reset()
    time.sleep(1)


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
    
    print("schedule enabled status changed and saved to file") 

def handle_remove_rack(msg_data):
    global bins
    
    new_rack = {
        "rack_id": "",
        "master": "",
        "bins": []
    }
    led_pins = [12, 25, 26, 27]
    button_pins = [13, 14, 15, 16]
    bin_count = 4
    new_rack['bins'] = [
        {
            "color":[0, 0, 0],
            "led_pin": led_pins[i],
            "bin_id": f"0{i+1}",
            "button_pin": button_pins[i],
            "enabled": True,
            "schedules": [],
            "clicked": False
        }
        for i in range(bin_count)
    ]
    

    with open('slave.json', 'w') as f:
        ujson.dump(new_rack, f)
        print("write Success")
    with open('sch.json', 'w') as f:
        ujson.dump({}, f)
        print("write Success2")
    time.sleep(1)
    machine.reset()

def handle_remove_schedule(msg_data):
    """
    Removes a schedule from a bin's schedule list.
    
    :param msg_data: A dictionary containing the 'bin_id' and 'schedule_time' to remove.
    """
    global bins

    bin_id = msg_data['bin_id']
    scheduled_time = msg_data['scheduled_time']

    for bin in bins:
            if bin['bin_id'] == bin_id:
                original_schedules = bin.get('schedules', [])
                
                # Filter out the schedule with the specified time
                updated_schedules = [schedule for schedule in original_schedules if schedule['time'] != scheduled_time]
                
                if len(original_schedules) > len(updated_schedules):
                    # Update the bin schedules in config and bins
                    bin['schedules'] = updated_schedules
                    config['bins'] = bins
                    
                    # Write updated data back to slave.json
                    with open('slave.json', 'w') as f:
                        ujson.dump(config, f)
                    print(f"Schedule at {scheduled_time} removed from bin {bin_id} and saved to file.")
                else:
                    print(f"No schedule found at {scheduled_time} for bin {bin_id}.")
                break
def espnow_listener(e,config, rack_id):
    global bins, message_queue, avail, rtc, global_time
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
                if not print("F2") and msg == b'avail':
                    avail = True
                    send_messages_from_queue()
                    continue

                elif not print("F3") and msg == b'unavail':
                    avail = False
                    print("Availability set to False")
                    continue
                elif not print("F4") and "999999" in msg:
                    print("Received message from peer:", msg)
                    global_time = msg.decode()
                    hour, minute, second, dummy = map(int, global_time.split(":"))
                    rtc.datetime((2024, 8, 3, 6, hour, minute, second, 0))
                    continue

                try:
                    print("F4")
                    msg_data = ujson.loads(msg)
                    operation = msg_data.get('operation')
                    print("F5")
                    if not print("F6") and operation == 'push':
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
                    elif operation == 'remove-rack':
                        handle_remove_rack(msg_data)
                    elif operation == 'remove-schedule':
                        handle_remove_schedule(msg_data)
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
            

        time.sleep(1)  # Minimal delay to keep the system running
 
def send_messages_from_queue():
    global message_queue, e ,master_mac
    #print(message_queue)
    
    while message_queue:
        master_mac, msg = message_queue.pop(0)
        print(master_mac, msg)
        try:
            e.add_peer(bytes(master_mac))
        except Exception:
            print("Already added.")
        e.send(bytes(master_mac), msg)
        print(f"Sent message from queue to {master_mac}: {msg}")
config, master_mac, rack_id, e = None, None, None, None


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

def get_data():
    data = []
    with open("slave.json", 'r') as f:
        data= ujson.load(f)
    
    return data;

def schedule_checker():
    print("Called")
    global bins, rtc, config
    while True:
        
        config = get_data();
        if not config:
            return 

        current_time = rtc.datetime()

        print(current_time)
        current_hour = str(current_time[4]) # Ensure hour and minute are two digits
        current_minute = str(current_time[5])

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
e = None
config = {}
master_mac = {}

def set_default_color():
    pins = [12, 25, 26, 27]
    neopixels = [NeoPixel(machine.Pin(pin), 10) for pin in pins]
    for np in neopixels:
        for i in range(np.n):
            np[i] = (0, 0, 0)  # Set each LED to (0, 0, 0)
        np.write()  # Update the LEDs with the new color

set_default_color()

try:
    config = read_config()

    time.sleep(3)
    master_mac = config['master']
    time.sleep(3)
    rack_id = config['rack_id']
    time.sleep(3)


    

    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    print("WiFi and ESP-NOW initialized.")
    
    e = espnow.ESPNow()
    e.active(True)

    time.sleep(3)


    try:
        if master_mac:
            e.add_peer(master_mac)
        else:
            pass
        time.sleep(3)
    except Exception  as err:
        print("Already added." , err)

    time.sleep(3)

    _thread.start_new_thread(espnow_listener, (e,config, rack_id))

    bins = [Bin(bin_config, i, rack_id, e, master_mac) for i, bin_config in enumerate(config['bins'])]


    if bins:
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
        hour, minute, second = map(int, global_time.split(":"))
        rtc.datetime((2024, 8, 3, 6, hour, minute, second, 0))
        time.sleep(2)
        schedule_checker()
    


except Exception as err:
    print(err)

    machine.reset()

    










