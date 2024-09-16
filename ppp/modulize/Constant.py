# Constant.py
import machine
import time
from ds3231 import DS3231  # Replace with actual import if necessary



class Constants:
    def __init__(self):
        # I2C Configuration
        self._sda_pin = machine.Pin(21)
        self._scl_pin = machine.Pin(22)
        self._i2c = machine.I2C(0, scl=self._scl_pin, sda=self._sda_pin)
        #time.sleep(0.5)  # Short delay to ensure I2C is ready

        # Initialize DS3231 RTC module
        self._rtc = DS3231(self._i2c)

        # Buzzer and Relay Configuration
        self._buzzer_pin = 32
        self._relay_pin = 33
        self._buzzer = machine.Pin(self._buzzer_pin, machine.Pin.OUT)
        self._relay = machine.Pin(self._relay_pin, machine.Pin.OUT)

        # Shared state
        self._active_bins = []

        # Default values for variables
        self._current_group_id = None
        self._current_rack = None
        self._group_index = None
        # self._bins = []

    # Getters
    def get_i2c(self):
        return self._i2c

    def get_rtc(self):
        return self._rtc

    def get_buzzer(self):
        return self._buzzer

    def get_relay(self):
        return self._relay

    def get_active_bins(self):
        return self._active_bins

    def get_current_group_id(self):
        return self._current_group_id

    def get_current_rack(self):
        return self._current_rack

    def get_group_index(self):
        return self._group_index

    # def get_bins(self):
    #     return self._bins

    # Setters
    def set_current_group_id(self, value):
        self._current_group_id = value

    def set_current_rack(self, value):
        self._current_rack = value

    def set_group_index(self, value):
        self._group_index = value

    # def set_bins(self, value):
    #     self._bins = value

    def add_to_active_bins(self, rack_id, bin_index,color):

        if (rack_id, bin_index) not in [(b[0], b[1]) for b in self._active_bins]:  # Check if (rack_id, bin_index) is not already in the list
            self._active_bins.append((rack_id, bin_index, color))
            print(f"Added bin {bin_index} in rack {rack_id} with color {color} to active bins.")
        
        self.check_and_update_buzzer_relay()

    def remove_from_active_bins(self, rack_id, bin_index):
        
        self._active_bins = [b for b in self._active_bins if not (b[0] == rack_id and b[1] == bin_index)]
        print(f"Removed bin {bin_index} in rack {rack_id} from active bins.")
        self.check_and_update_buzzer_relay()

    def check_and_update_buzzer_relay(self):
        if self._active_bins:
            # self._buzzer.on()
            self._relay.on()
            print("Buzzer and Relay turned ON")
        else:
            # self._buzzer.off()
            self._relay.off()
            print("Buzzer and Relay turned OFF")
