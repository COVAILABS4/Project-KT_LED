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

# Set current date and time
# Format: (year, month, day, hours, minutes, seconds)
current_time = (2024, 8, 3, 14, 26, 3, 0, 0)  # Added yday as 0

rtc.set_time(current_time[0], current_time[1], current_time[2], current_time[3], current_time[4], current_time[5], current_time[6], current_time[7])

# Verify by reading back the time
rtc_time = rtc.get_time()
print(f"RTC Time set to: {rtc_time}")

# Optional: Delay to keep the program running for a while
time.sleep(10)

