# get_time.py

import time
import machine
from ds3231 import DS3231

# Define I2C pins for SDA and SCL
sda_pin = machine.Pin(21)
scl_pin = machine.Pin(22)

# Initialize I2C
i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin)
time.sleep(0.5)  # Short delay to ensure I2C is ready

# Initialize the DS3231 RTC module
rtc = DS3231(i2c)



while True:
    rtc_time = rtc.get_time()
    print(f"RTC Time set to: {rtc_time[3]} : {rtc_time[4]} : {rtc_time[5]}")
    time.sleep(1)


