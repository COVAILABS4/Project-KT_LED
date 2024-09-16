#Bin.py

import machine
import time
import ujson
from neopixel import NeoPixel
from Constant import Constants

from file_operations import get_data,set_data
# import json
from QueueManager import QueueManager
# from Constant import Constants

QObject = QueueManager()

class Bin:
    def __init__(self, bin_config, index, rack_id,const):
        self.button_pin = bin_config['button_pin']
        self.led_pin = bin_config['led_pin']
        self.color = tuple(bin_config['color'])
        self.last_pressed_time = 0
        self.clicked = bin_config['clicked']
        self.enabled = bin_config['enabled']
        self.schedules = bin_config['schedules']
        self.index = index  # Store the index
        self.rack_id = rack_id
        self.const = const

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
            self.clicked = True  # Toggle clicked state

        
            self.turn_off_leds()
            self.const.remove_from_active_bins(self.rack_id, self.index)  # Remove from active bins

            # Send button press status to master
            self.send_message(self.index, 'click-change')
            self.const.check_and_update_buzzer_relay()  # Check buzzer and relay status after button press

    def send_message(self, bin_index, operation):
        msg = {
            'rack_id': self.rack_id,
            'bin_idx': bin_index,
            'operation': operation
        }
        self.update_data_json_from_message(msg)
        print(f"Sent message: {msg}")

    def update_data_json_from_message(self,msg_data):
        # cur
    
        data = get_data()
        try:
            # msg_data = json.loads(msg)
            rack_id = msg_data.get('rack_id')
            bin_idx = msg_data.get('bin_idx')
            operation = msg_data.get('operation')
            print(rack_id, bin_idx)
            
            if not rack_id or bin_idx is None:
                print("Error: Missing required fields in the message")
                return


            group_id = None

            if operation=="click-change":
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
        
                                group_id = group['Group_id']
                            else:
                                print(f"Error: Bin index {bin_idx} out of range")
                            break
                    print(group_id,"---",rack_id,"---",bin_idx)
                    
                    
            set_data(data)


            print("Data JSON updated based on received message")

            # Add notification to queue
            QObject.add_notify_queue({
                'group_id': self.const._current_group_id,
                'rack_id': rack_id,
                'bin_idx': bin_idx,
                'operation': operation,
            })
        
        except Exception as err:
            print(f"Error updating JSON from message: {err}")
