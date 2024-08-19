import socket
import network
import time
SSID = "AB7"

PASSWORD = "07070707"

wlan = network.WLAN(network.STA_IF)

def connect_wifi():
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Connecting to WiFi", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(1)
    print()
    print("Connected to WiFi:", wlan.ifconfig())

def disconnect_wifi():
    wlan.disconnect();
    print("Disconnect the Wifi")
    
    
def start_http_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print('HTTP server listening on', addr)

    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)
        cl_file = cl.makefile('rwb', 0)
        while True:
            line = cl_file.readline()
            if not line or line == b'\r\n':
                break
        response = b"HTTP/1.1 200 OK\r\n\r\nHello, World!"
        cl.send(response)
        cl.close()
        break
        #break  # Stop after one connection for demo purposes
    
    s.close()
    print("HTTP server stopped.")
    

connect_wifi()
for i in range(10):
    
    start_http_server()
    

