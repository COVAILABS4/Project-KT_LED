import time
import machine
import network
import espnow
from ds3231 import DS3231



#--------------------------master----------------------------



# Define I2C pins for SDA and SCL
sda_pin = machine.Pin(21)
scl_pin = machine.Pin(22)

# Initialize I2C
i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin)
time.sleep(0.5)  # Short delay to ensure I2C is ready

# Initialize the DS3231 RTC module
rtc = DS3231(i2c)

# Initialize Wi-Fi and ESP-NOW
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()   # Disconnect from any Access Point

e = espnow.ESPNow()
e.active(True)

# Optionally, add a peer if you have specific peers
# e.add_peer(b'\xFF\xFF\xFF\xFF\xFF\xFF')  # Replace with the MAC address of the peer if needed

while True:
    host, msg = e.recv()
    if msg:  # msg == None if timeout in recv()
        print("Received message from:", host, "Message:", msg)
        if msg == b"get-time":
            # Get current time from RTC
            rtc_time = rtc.get_time()
            # Format the time to send
            response = f"{rtc_time[3]}:{rtc_time[4]}:{rtc_time[5]}".encode()
            # Send the current time back to the peer
            try:
                e.add_peer(host)
            except Exception:
                pass
            e.send(host, response)
    time.sleep(1)

