import network
import socket
import json
import machine


def setup_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='ESP32-AP', password='12345678', channel=1, authmode=network.AUTH_WPA_WPA2_PSK)
    while not ap.active():
        pass
    print('AP Mode configured:', ap.ifconfig())
    return ap
setup_access_point()

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
    ap = setup_access_point()
    config = load_config()
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

    try:
        s_ap = socket.socket()
        try:
            s_ap.bind(addr)
        except Exception:
            machine.reset()
        s_ap.listen(5)
        print('Web server running on http://0.0.0.0:80')
    except OSError as err:
        print("Socket error:", err)
        return

    try:
        while True:
            try:
                client, addr = s_ap.accept()
                print('Client connected from', addr)
                handle_request(client, config)
                client.close()
            except OSError as err:
                print("Error while handling client:", err)
    finally:
        s_ap.close()
        teardown_access_point(ap)

start_server_AP()


