import network
import time
import machine
import urequests
from ds3231 import DS3231

# Define I2C pins for SDA and SCL
sda_pin = machine.Pin(21)
scl_pin = machine.Pin(22)

# Initialize I2C for RTC
i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin)
rtc = DS3231(i2c)

# WiFi connection credentials
SSID = 'AB7'
PASSWORD = '07070707'

# Connect to WiFi
def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    # Wait for connection
    while not wlan.isconnected():
        print("Connecting to WiFi...")
        time.sleep(1)
    
    print("Connected to WiFi. IP address:", wlan.ifconfig()[0])

# Function to set RTC time
def set_rtc_time(year, month, day, hour, minute, second):
    rtc.set_time(
        year, month, day, hour, minute, second, 0, 0
    )

# Function to parse ISO 8601 date and time string manually
def parse_iso_time(iso_string):
    # Example ISO 8601 format: "2024-08-03T14:26:03.000Z"
    date_time = iso_string.split("T")
    
    # Extract date
    date_parts = date_time[0].split("-")
    year = int(date_parts[0])
    month = int(date_parts[1])
    day = int(date_parts[2])
    
    # Extract time (ignoring milliseconds and 'Z')
    time_parts = date_time[1].split(":")
    hour = int(time_parts[0])
    minute = int(time_parts[1])
    second = int(time_parts[2].split(".")[0])
    
    return year, month, day, hour, minute, second

# Function to request time from server
def get_time_from_server():
    try:
        url = "http://192.168.138.83:5000/get-time"  # Replace with your server IP
        response = urequests.get(url)
        if response.status_code == 200:
            # Parse the time from the server response
            time_data = response.json().get('time')
            print(f"Received time from server: {time_data}")
            
            # Parse the ISO time string manually
            year, month, day, hour, minute, second = parse_iso_time(time_data)
            
            # Set the RTC with the new time
            set_rtc_time(year, month, day, hour, minute, second)
            print(f"RTC updated to: {year}-{month}-{day} {hour}:{minute}:{second}")
        else:
            print("Failed to get time from server")
    except Exception as e:
        print(f"Error fetching time: {e}")

# Main function
def main():
    # Connect to WiFi
    connect_to_wifi(SSID, PASSWORD)
    
    # Get time from the server and update RTC
    get_time_from_server()

# Run the main function
main()

# Keep the program running
while True:
    time.sleep(5)

