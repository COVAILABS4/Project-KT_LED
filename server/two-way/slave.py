import network
import espnow
import time
import machine

# Initialize WLAN as station
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()

# Initialize ESP-NOW
e = espnow.ESPNow()
e.active(True)

# Define peer MAC address (replace with the actual MAC address of ESP2)
peer_mac = b'H\xe7)\xa1\x90,'
e.add_peer(peer_mac)

# Initialize push button (assuming it's connected to GPIO 15)
button = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)

# Define the debounce delay in milliseconds
debounce_delay = 200  # Adjust as necessary

# Last time the button was pressed
last_pressed_time = 0

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

# Interrupt handler for button press
def button_handler(pin):
    global last_pressed_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_pressed_time) > debounce_delay:
        send_message("Clicked")
        last_pressed_time = current_time

# Attach interrupt to the button pin
button.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_handler)

# Main loop
while True:
    # Check for incoming messages
    msg = receive_message()
    if msg:
        # Handle received message (if any)
        print(f"Message received: {msg}")

    # Sleep to reduce CPU usage
    time.sleep(0.1)

