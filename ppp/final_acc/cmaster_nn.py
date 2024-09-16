#----------------------AP Setup -------------------#
import network
import socket
import json
import machine

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

def render_html(template, config):
    global local_ip
    print(local_ip)
    for key, value in config.items():
        template = template.replace('{{' + key + '}}', value)
    
    template = template.replace('{{IP_ADDRESS}}', local_ip)
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
        with open('intex.txt', 'r') as f:
            html = f.read()
        response = render_html(html, config)
        client.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'.encode('utf-8'))
        client.send(response.encode('utf-8'))
        
        
def start_server_AP():
    ap = setup_access_point()  # Setup the Access Point
    config = load_config()     # Load the configuration
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

    try:
        s_ap = socket.socket()  # Create a new socket
        try:
            s_ap.bind(addr)     # Bind to the address and port
        except Exception as bind_error:
            print(f"Socket binding failed: {bind_error}")
            machine.reset()     # Resetting device if binding fails
        s_ap.listen(5)          # Start listening for clients
        print('Web server running on http://0.0.0.0:80')
    except OSError as err:
        print("Socket error during setup:", err)
        return

    try:
        while True:
            try:
                client, client_addr = s_ap.accept()  # Accept a client connection
                print('Client connected from', client_addr)
                handle_request(client, config)       # Handle the client request
            except OSError as client_err:
                print("Error while handling client:", client_err)
            finally:
                client.close()  # Ensure the client socket is closed after handling
    finally:
        s_ap.close()           # Close the server socket
        teardown_access_point(ap) 


# if 
setup_access_point()


start_server_AP()





