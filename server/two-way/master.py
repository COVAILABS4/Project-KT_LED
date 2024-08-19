import network
import espnow
import time

# Initialize WLAN as station
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()

# Initialize ESP-NOW
e = espnow.ESPNow()
e.active(True)

# Define peer MAC address (replace with the actual MAC address of ESP1)
peer_mac = b'\xa8B\xe3L\xc0H'
e.add_peer(peer_mac)

# Function to send messages to peer
def send_message(msg):
    e.send(peer_mac, msg)
    print(f"Sent: {msg}")

# Function to receive messages from peer
def receive_message():
    host, msg = e.recv()
    if msg:
        print(f"Received from {host}: {msg}")
        return msg

# Main loop
count = 1
while True:
    if count <= 10:
        # Send count message to ESP1
        send_message(str(count))
        count += 1
        time.sleep(1)  # Delay for 1 second
    else:
        # Reset count after 10
        count = 1

    # Check for incoming messages
    msg = receive_message()
    if msg:
        # Handle received message (if any)
        print(f"Message received: {msg}")

    time.sleep(1)  # Delay for demonstration

