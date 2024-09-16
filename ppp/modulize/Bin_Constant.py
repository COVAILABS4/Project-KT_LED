
# Bin_Constant.py

import machine
import time
from ds3231 import DS3231  # Replace with actual import if necessary

class Bin_Constants:
    def __init__(self):
        
        self._bins = []
        
    def set_bins(self, value):
        self._bins = value
