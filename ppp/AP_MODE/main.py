import json
import network
import usocket as socket
import machine
from neopixel import NeoPixel
import esp
import gc
import time

gc.enable()
def set_default_color():
    pins = [12, 25, 26, 27]
    neopixels = [NeoPixel(machine.Pin(pin), 10) for pin in pins]
    for np in neopixels:
        for i in range(np.n):
            np[i] = (0, 0, 0)  # Set each LED to (0, 0, 0)
        np.write()  # Update the LEDs with the new color

set_default_color()




def setup_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    wlan_mac = ap.config('mac')
    mac_arr = [str(i) for i in wlan_mac]
    
    # print(mac_arr)
    
    MAC_ADD = mac_arr[-2:]

    MAC_STR = "".join(MAC_ADD)
    
    # print(MAC_STR)
    
    ap.config(essid='ESP32-'+MAC_STR, password='12345678', channel=1, authmode=network.AUTH_WPA_WPA2_PSK)
    while not ap.active():
        pass
    print('AP Mode configured:', ap.ifconfig())
    return ap



def teardown_access_point(ap):
    ap.active(False)
    print("Access Point deactivated.")

def teardown_wifi(sta):
    # Initiate disconnection
    sta.disconnect()
    
    # Wait until the station is disconnected
    while sta.isconnected():
        print("Waiting for Wi-Fi to disconnect...")
        time.sleep(1)
    
    # Deactivate Wi-Fi once fully disconnected
    sta.active(False)
    print("Wi-Fi disconnected and deactivated.")


local_ip = "192.168.4.1"

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return {"KIT_NO": "", "STATIC_NO": "", "SERVER_NO": "", "SSID": "", "PASSWORD": ""}

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f)

def render_html(template, config, ip):
    global local_ip
    
    local_ip = ip
    for key, value in config.items():
        template = template.replace('{{' + key + '}}', value)
    
    print("TP - - 1")
    # static_no = str("120")
    if local_ip is not None:
        #print(local_ip)
        local_ip = local_ip.split(".")
        
        local_ip =  ".".join(local_ip[:-1])
        print("TF - 2")
        local_ip = local_ip + "." + config['STATIC_NO']
        print("TF - 3")
    else: 
        local_ip = "EMPTY"
    print("TP - - 2")       
    template = template.replace('{{IP_ADDRESS}}', local_ip )
    print("TF - 4")
    return template

def url_decode(url_encoded_str):
    """Manually decode a URL-encoded string."""
    result = url_encoded_str.replace('+', ' ')
    parts = result.split('%')
    decoded_str = parts[0]
    for part in parts[1:]:
        try:
            decoded_str += chr(int(part[:2], 16)) + part[2:]
        except ValueError:
            decoded_str += '%' + part
    return decoded_str

def parse_form_data(body):
    """Parse URL-encoded form data."""
    data = {}
    pairs = body.split('&')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            data[url_decode(key)] = url_decode(value)
    return data

def connect_to_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    # If already connected, disconnect first
    if sta.isconnected():
        print("Already connected, disconnecting...")
        sta.disconnect()
    
    # Connect to the Wi-Fi network
    print(f"Connecting to {ssid}...")
    sta.connect(ssid, password)
    
    timeout = 10
    while not sta.isconnected() and timeout > 0:
        timeout -= 1
        time.sleep(1)
    
    # Check if the connection was successful
    if sta.isconnected():
        ip = sta.ifconfig()[0]
        print(f"Connected successfully, IP address: {ip}")
        return ip
    else:
        print("Failed to connect.")
        return None


def handle_request(client, config):
    request = client.recv(1024).decode('utf-8')
    if 'POST /update' in request:
        body = request.split('\r\n\r\n')[1]
        params = parse_form_data(body)
        config.update(params)
        save_config(config)
        response = 'HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n'
        client.send(response.encode('utf-8'))
    else:
        with open('index.txt', 'r') as f:
            html = f.read()
        ip_address = None
        try:
            ip_address = connect_to_wifi(config['SSID'], config['PASSWORD'])
        except Exception as err:
            print("ERROR : ",err)
        response = render_html(html, config, ip_address)
        client.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'.encode('utf-8'))
        client.send(response.encode('utf-8'))
        if ip_address:
            teardown_wifi(network.WLAN(network.STA_IF))
        
        
def start_server_AP():
    ap = setup_access_point()  # Setup the Access Point
    config = load_config()     # Load the configuration
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s_ap = None
    try:
        s_ap = socket.socket()  # Create a new socket
        try:
            s_ap.bind(addr)     # Bind to the address and port
        except Exception as bind_error:
            print(f"Socket binding failed: {bind_error}")
            machine.reset()     # Resetting device if binding fails
        s_ap.listen(5)          # Start listening for clients
        print('Web server running on http://192.168.4.1:80')
    except OSError as err:
        print("Socket error during setup:", err)
        return
    client = None
    try:
        while True:
            print("TP 1")
            try:
                client, client_addr = s_ap.accept()  # Accept a client connection
                print('Client connected from', client_addr)
                handle_request(client, config)       # Handle the client request
            except OSError as client_err:
                print("Error while handling client:", client_err)
            finally:
                if client is not None:
                    client.close()  # Ensure the client socket is closed after handling
    finally:
        if s_ap is not None and ap is not None:
            s_ap.close()           
            print("TP 2")
            teardown_access_point(ap)

try:
    setup_access_point()
    start_server_AP()
except Exception as err:
    print(err)





