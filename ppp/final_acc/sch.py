import machine
import time
import json
import os
from neopixel import NeoPixel
import _thread

rtc = machine.RTC()

# Define pin numbers
led_pins = [12, 25, 26, 27]
button_pins = [13, 14, 15, 16]
buzzer_pin = 32
relay_pin = 33

# Initialize buzzer and relay
buzzer = machine.Pin(buzzer_pin, machine.Pin.OUT)
relay = machine.Pin(relay_pin, machine.Pin.OUT)

# Load schedule from JSON file
def load_schedule():
    if 'sch.json' in os.listdir():
        with open('sch.json', 'r') as f:
            return json.load(f)
    else:
        return {}

schedules = load_schedule()

# Shared state for buzzer and relay management
task_dict = {}

class Bin:
    def __init__(self, bin_index, led_pin, button_pin):
        self.bin_index = bin_index
        self.led = NeoPixel(machine.Pin(led_pin), 5)  # Assuming one LED per bin
        self.button = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.button_pressed = False
        self.last_pressed_time = 0
        self.debounce_delay = 200  # 200 milliseconds debounce delay

        # Initialize the button interrupt
        self.button.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.handle_button_press)

    def set_color(self, color):
        for i in range(5):
            self.led[i] = color
        self.led.write()

    def turn_off_led(self):
        for i in range(5):
            self.led[i] = (0, 0, 0)
        self.led.write()

    def handle_button_press(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_pressed_time) > self.debounce_delay:
            print(f"Button pressed on pin {pin}")
            self.last_pressed_time = current_time
            self.button_pressed = True
            self.turn_off_led()
            self.update_task_dict(False)  # Remove task from dictionary
            # Manage buzzer and relay state
            if not task_dict:
                buzzer.off()
                relay.off()

    def wait_for_button_press(self, timeout=10):
        start_time = time.time()
        self.button_pressed = False
        while time.time() - start_time < timeout:
            if self.button_pressed:
                self.button_pressed = False
                return True
            time.sleep(0.1)
        return False

    def sound_buzzer_and_relay_until_button_press(self):
        if task_dict:
            buzzer.on()
            relay.on()
        self.wait_for_button_press()
        if not task_dict:
            buzzer.off()
            relay.off()

    def update_task_dict(self, add_task=True):
        global task_dict
        if add_task:
            task_dict[self.bin_index] = True
        else:
            if self.bin_index in task_dict:
                del task_dict[self.bin_index]

# Initialize bins
bins = [Bin(i, led_pins[i], button_pins[i]) for i in range(len(led_pins))]

# Function to handle individual schedule
def handle_schedule(bin_index, color):
    bins[bin_index].set_color(color)
    bins[bin_index].update_task_dict(True)  # Add task to dictionary
    # Wait for 30 seconds to check if the button is pressed
    if not bins[bin_index].wait_for_button_press():
        print(f"Button {bin_index} not pressed within 30 seconds, sounding buzzer and turning on relay")
        bins[bin_index].sound_buzzer_and_relay_until_button_press()
    print(f"Button {bin_index} pressed, turning off LED, buzzer, and relay")

# Function to check schedules
def check_schedules():
    global rtc
    current_time = rtc.datetime()
    print("Current time: {:02}:{:02}:{:02}".format(current_time[4], current_time[5], current_time[6]))

    current_hour = current_time[4]
    current_minute = current_time[5]

    current_minute = str(current_minute)
    if len(current_minute) < 2:
        current_minute = '0' + current_minute
    print(current_minute)

    if str(current_hour) in schedules and current_minute[0] in schedules[str(current_hour)]:
        print("Schedule found")
        for schedule in schedules[str(current_hour)][current_minute[0]]:
            if str(current_hour) + ":" + current_minute in schedule['scheduleTime']:
                bin_index = schedule["index"]
                color = tuple(schedule["color"])
                print(f"Setting LED {bin_index} to color {color}")
                _thread.start_new_thread(handle_schedule, (bin_index, color))

# Main function
def main():
    global rtc
    # Set the RTC with the provided time
    time_str = "16:01:50"
    hour, minute, second = map(int, time_str.split(':'))

    # Get the current date
    current_date = rtc.datetime()
    year, month, day, weekday = current_date[:4]
    # Set the new time with the provided hour, minute, and second
    rtc.datetime((year, month, day, weekday, hour, minute, second, 0))

    # Continuously check schedules every 1 minute
    time.sleep(15)
    while True:
        check_schedules()
        time.sleep(60)

# Run the main function
main()

