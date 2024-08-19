import time
import machine
import network
import espnow

# Initialize Wi-Fi and ESP-NOW
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()   # Disconnect from any Access Point

e = espnow.ESPNow()
e.active(True)

# Optionally, add a peer if you have specific peers
# e.add_peer(b'\xFF\xFF\xFF\xFF\xFF\xFF')  # Replace with the MAC address of the peer if needed

# Initialize RTC
rtc = machine.RTC()

# Global variable to store the received time
global_time = None

def display_time():
    while True:
        current_time = rtc.datetime()
        print("Current time: {:02}:{:02}:{:02}".format(current_time[4], current_time[5], current_time[6]))
        time.sleep(1)
def send_request():
    # Send the "get-time" request to the peer
    peer = bytes([44,
          188,
          187,
          5,
          23,
          36])
    try:
        e.add_peer(peer)
    except Exception:
        pass
    e.send(peer, b"get-time")  # Broadcast or specify peer MAC address
    print("Sent request for time")

def update_time_from_peer():
    global global_time
    while global_time is None:
        send_request()
        isGet = True
        while isGet:
            host, msg = e.recv()
            if msg:
                print(host, msg)
                isGet = False
        if msg:
            global_time = msg.decode()
            print("Received time from peer:", global_time)
            # Set the RTC with the received time
            hour, minute, second = map(int, global_time.split(":"))
            rtc.datetime((2024, 8, 3, 6, hour, minute, second, 0))
            display_time()
            break
        else:
            print("No response received, retrying...")
    
    # If you need to reset the global_time after updating, uncomment the following line
    # global_time = None

while True:
    update_time_from_peer()
    time.sleep(60)  # Update time every 60 seconds

