import json
import network
import usocket as socket
import machine
from neopixel import NeoPixel
import esp
import gc
gc.enable()

#Define the pin for the switch
switch_pin = machine.Pin(2, machine.Pin.IN)

curr_state = switch_pin.value()


if curr_state == 1:  
    try:
        with open('sam4.py', 'r') as file:
            code = file.read()
        exec(code)
    except Exception:
        
        machine.reset()

elif curr_state == 0:
    try:
        with open('sam2.py', 'r') as file:
            code = file.read()
        exec(code)
    except Exception:
        
        machine.reset()
        



