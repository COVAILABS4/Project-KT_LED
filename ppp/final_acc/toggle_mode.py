import network
import socket
import json
import os
import time

CONFIG_FILE = "config.json"

def load_config():
    """Load the configuration from the JSON file."""
    if CONFIG_FILE in os.listdir():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Initialize default configuration if file does not exist
        return {
            "ap_ssid": "ESP32_AP",
            "ap_password": "password",
            "ap_ip": "192.168.4.1",
            "sta_ssid": "",
            "sta_password": "",
            "sta_ip": ""
        }

def save_config(config):
    """Save the updated configuration to the JSON file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def setup_ap_mode(config):
    """Set up Access Point mode."""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.ifconfig((config["ap_ip"], '255.255.255.0', config["ap_ip"], config["ap_ip"]))
    ap.config(essid=config["ap_ssid"], password=config["ap_password"])
    return ap

def setup_sta_mode(config):
    """Set up Station mode with DHCP or static IP based on configuration."""
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    # Apply static IP if provided
    if config.get("sta_ip"):
        sta.ifconfig((config["sta_ip"], '255.255.255.0', '192.168.1.1', '8.8.8.8'))  # Replace with your gateway and DNS if necessary

    # Log the connection attempt
    print("Connecting to SSID: {}".format(config["sta_ssid"]))
    sta.connect(config["sta_ssid"], config["sta_password"])

    # Retry mechanism with timeout
    max_attempts = 10
    attempt = 0
    while not sta.isconnected() and attempt < max_attempts:
        print("Connecting to WiFi... Attempt {}".format(attempt + 1))
        attempt += 1
        time.sleep(1)  # Wait for a second before retrying
    
    # Check if connected and provide connection details
    if sta.isconnected():
        print("Connected to WiFi. IP: {}".format(sta.ifconfig()[0]))
        return sta
    else:
        print("Failed to connect to WiFi after {} attempts.".format(max_attempts))
        sta.active(False)
        return None

def stop_ap_mode(ap):
    """Deactivate Access Point mode."""
    if ap.active():
        print("Deactivating AP mode...")
        ap.active(False)

def start_server(ap_mode=True):
    """Start the HTTP server."""
    global server_socket
    if server_socket:
        server_socket.close()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('', 80))
    except Exception as e:
        print(f"Failed to bind server socket: {e}")
        return
    server_socket.listen(5)
    
    print("Server started on mode: {}".format("AP" if ap_mode else "STA"))

    while True:
        try:
            conn, addr = server_socket.accept()
            print('Got a connection from %s' % str(addr))
            request = conn.recv(1024)
            request = str(request)
            print('Content = %s' % request)
            
            response = handle_request(request, ap_mode)
            conn.send(response.encode())
            conn.close()
        except Exception as e:
            print(f"Server error: {e}")
            continue

def handle_request(request, ap_mode):
    """Handle incoming HTTP requests based on the mode."""
    if ap_mode:
        if 'GET /set-sta-ssid-password' in request:
            return handle_set_sta_ssid_password(request)
        elif 'GET /get-sta-ssid-password' in request:
            return handle_get_sta_ssid_password()
        elif 'GET /set-sta-ip' in request:
            return handle_set_sta_ip(request)
        elif 'GET /get-sta-ip' in request:
            return handle_get_sta_ip()
        elif 'GET /change_to_sta' in request:
            return handle_change_to_sta()
    else:
        if 'GET /set-ap-ssid-password' in request:
            return handle_set_ap_ssid_password(request)
        elif 'GET /get-ap-ssid-password' in request:
            return handle_get_ap_ssid_password()
        elif 'GET /set-ap-ip' in request:
            return handle_set_ap_ip(request)
        elif 'GET /get-ap-ip' in request:
            return handle_get_ap_ip()
        elif 'GET /change_to_ap' in request:
            return handle_change_to_ap()

    return 'HTTP/1.1 404 Not Found\n\nResource not found'

def handle_set_sta_ssid_password(request):
    """Handle setting STA SSID and password."""
    try:
        params = request.split(' ')[1].split('?')[1].split('&')
        ssid = params[0].split('=')[1]
        password = params[1].split('=')[1]
        config["sta_ssid"] = ssid
        config["sta_password"] = password
        save_config(config)
        return 'HTTP/1.1 200 OK\n\nSTA SSID and Password set'
    except Exception as e:
        print(f"Error setting STA SSID and Password: {e}")
        return 'HTTP/1.1 400 Bad Request\n\nError setting STA SSID and Password'

def handle_get_sta_ssid_password():
    """Handle getting STA SSID and password."""
    return 'HTTP/1.1 200 OK\n\n{}'.format(json.dumps({"sta_ssid": config["sta_ssid"], "sta_password": config["sta_password"]}))

def handle_set_sta_ip(request):
    """Handle setting STA IP."""
    try:
        ip = request.split(' ')[1].split('?')[1].split('=')[1]
        config["sta_ip"] = ip
        save_config(config)
        
        # Apply the new static IP setting
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.ifconfig((config["sta_ip"], '255.255.255.0', '192.168.1.1', '8.8.8.8'))  # Replace with your gateway and DNS if necessary

        return 'HTTP/1.1 200 OK\n\nSTA IP set to {}'.format(ip)
    except Exception as e:
        print(f"Error setting STA IP: {e}")
        return 'HTTP/1.1 400 Bad Request\n\nError setting STA IP'

def handle_get_sta_ip():
    """Handle getting STA IP."""
    return 'HTTP/1.1 200 OK\n\n{}'.format(config.get("sta_ip", ""))

def handle_change_to_sta():
    """Handle changing from AP mode to STA mode."""
    global ap
    stop_ap_mode(ap)  # Deactivate AP mode
    
    sta = setup_sta_mode(config)
    if sta and sta.isconnected():
        start_server(ap_mode=False)  # Restart server in STA mode
        return 'HTTP/1.1 200 OK\n\nChanged to STA mode'
    else:
        return 'HTTP/1.1 500 Internal Server Error\n\nFailed to change to STA mode'

def handle_set_ap_ssid_password(request):
    """Handle setting AP SSID and password."""
    try:
        params = request.split(' ')[1].split('?')[1].split('&')
        ssid = params[0].split('=')[1]
        password = params[1].split('=')[1]
        config["ap_ssid"] = ssid
        config["ap_password"] = password
        save_config(config)
        return 'HTTP/1.1 200 OK\n\nAP SSID and Password set'
    except Exception as e:
        print(f"Error setting AP SSID and Password: {e}")
        return 'HTTP/1.1 400 Bad Request\n\nError setting AP SSID and Password'

def handle_get_ap_ssid_password():
    """Handle getting AP SSID and password."""
    return 'HTTP/1.1 200 OK\n\n{}'.format(json.dumps({"ap_ssid": config["ap_ssid"], "ap_password": config["ap_password"]}))

def handle_set_ap_ip(request):
    """Handle setting AP IP."""
    try:
        ip = request.split(' ')[1].split('?')[1].split('=')[1]
        config["ap_ip"] = ip
        save_config(config)
        
        # Apply the new static IP setting
        ap = network.WLAN(network.AP_IF)
        ap.ifconfig((config["ap_ip"], '255.255.255.0', config["ap_ip"], config["ap_ip"]))

        return 'HTTP/1.1 200 OK\n\nAP IP set to {}'.format(ip)
    except Exception as e:
        print(f"Error setting AP IP: {e}")
        return 'HTTP/1.1 400 Bad Request\n\nError setting AP IP'

def handle_get_ap_ip():
    """Handle getting AP IP."""
    return 'HTTP/1.1 200 OK\n\n{}'.format(config.get("ap_ip", ""))

def handle_change_to_ap():
    """Handle changing from STA mode to AP mode."""
    global sta
    if sta:
        sta.active(False)  # Deactivate STA mode
    
    ap = setup_ap_mode(config)
    start_server(ap_mode=True)  # Restart server in AP mode
    return 'HTTP/1.1 200 OK\n\nChanged to AP mode'

# Initialize
config = load_config()
ap = setup_ap_mode(config)

sta  = None
server_socket = None
start_server(ap_mode=True)

