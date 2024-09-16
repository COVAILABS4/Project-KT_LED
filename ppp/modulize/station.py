
#station.py

import socket
import time
import json
import requests
import machine
import network

from utils import handle_operation

from QueueManager import QueueManager

# from utils import handle_operation


QM_Object = QueueManager()


# def handle_operation(sev_data,mac,const):

#     print(sev_data,mac,const)


class Station:
    def __init__(self, ssid, password, static_ip, server_no,const ,bin_const):
        self.ssid = ssid
        self.password = password
        self.static_ip = static_ip
        self.server_no = server_no
        self.server_ip = None
        self.sta = None
        self.isAvail = False
        self.const = const
        self.bin_const = bin_const
        self.wlan_mac = ""
    

    def set_wlan_mac(self):
        mac = network.WLAN(network.STA_IF)
        mac.active(True)
        self.wlan_mac = mac.config('mac')
        
        
    def start_sta(self):
        """Initialize Wi-Fi station."""
        self.sta = network.WLAN(network.STA_IF)
        
        # Activate the Wi-Fi interface
        self.sta.active(True)

        # self.wlan_mac = self.sta.config('mac')

        
        # Check if the station is connected
        if self.sta.isconnected():
            print("Already connected, disconnecting...")
            self.sta.disconnect()  # Disconnect from the current Wi-Fi
            # Wait for the disconnection to complete
            while self.sta.isconnected():
                pass  # Wait until fully disconnected
            print("Disconnected.")
            machine.reset()
        else:
            print("Wi-Fi is already disconnected.")
        
        # Proceed with connection logic
        
        # print(f"MAC Address: {self.wlan_mac}")


        

    def connect_to_wifi(self):
        """Connect to the Wi-Fi network and handle IP extraction and modification."""
        self.start_sta()
        if not self.sta.isconnected():
            print('Connecting to network', end="")
            self.sta.connect(self.ssid, self.password)
            
            # self.sta.active(True)
            start_time = time.time()
            while not self.sta.isconnected():
                print(".", end="")
                time.sleep(1)
                if time.time() - start_time > 10:
                    print("\nFailed to connect within 10 seconds.")
                    machine.reset()
                    return
            print()

        print('Network configuration:', self.sta.ifconfig())
        self.update_ip()

    def update_ip(self):
        """Update IP address after Wi-Fi connection."""
        ip_info = self.sta.ifconfig()
        print("Current IP info:", ip_info)
        ip_address = ip_info[0]
        ip_parts = ip_address.split('.')

        if len(ip_parts) == 4:
            # Assign new static IP
            new_ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{self.static_ip}"
            self.server_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{self.server_no}"
            
            # Reconfigure network interface
            self.sta.ifconfig((new_ip_address, ip_info[1], ip_info[2], ip_info[3]))
            
            # Double check after update
            time.sleep(2)  # Short wait to ensure it's applied
            new_ip_info = self.sta.ifconfig()
            print('Updated network configuration:', new_ip_info)
            
            # Check if it was successfully updated
            if new_ip_info[0] == new_ip_address:
                print("IP updated successfully.")
            else:
                print("IP update failed.")
        else:
            print("Unexpected IP address format.")


    def disconnect_wifi(self):
        """Disconnect from the Wi-Fi network."""
        if self.sta.isconnected():
            print("Disconnecting Wi-Fi...")
            self.sta.disconnect()
            
            # Wait for the disconnection to complete
            while self.sta.isconnected():
                pass  # Wait until fully disconnected
            
            print("Wi-Fi disconnected")
        
        # Deactivate the Wi-Fi interface
        self.sta.active(False)
        print("Wi-Fi interface deactivated.")


    def get_mac(self):
        
        return self.wlan_mac
    

    def print_static(self):

        print(f'{self.ssid} - {self.password} - {self.server_no} - {self.static_ip} - {self.server_ip} - {self.wlan_mac}')


    def start_server(self):
        """Start the server and listen for client connections."""
        try:
            addr = socket.getaddrinfo("0.0.0.0", 8000)[0][-1]
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setblocking(False)
            s.bind(addr)
            s.listen(1)
            print('Listening on', addr)

            time.sleep(2)
            start_time = time.time()  # Record the start time

            while True:
                elapsed_time = time.time() - start_time
                if elapsed_time >= 600:  # Stop server after 20 seconds
                    print("Stopping server after 20 seconds.")
                    break

                try:
                    cl, addr = s.accept()
                    print('Client connected from', addr)
                    self.handle_client(cl)
                except OSError as err:
                    if err.errno == 11:  # EAGAIN, no client connected
                        time.sleep(0.1)
                    else:
                        print(f"Error processing request: {err}")
                        machine.reset()
                except TimeoutError:
                    print("Server timeout reached while processing request.")
                    break
        finally:
            if s is not None:
                s.close()
            print("Server has been shut down.")

    def handle_client(self, cl):
        """Handle client connections and process requests."""
        cl.setblocking(False)
        cl_file = cl.makefile('rwb', 0)

        try:
            # Read request line
            request_line = self.non_blocking_read(cl_file, delimiter=b'\r\n')
            method, path, version = request_line.decode('utf-8').strip().split()
            print(f"Received {method} request for {path}")

            # Read headers
            headers = {}
            header_line = self.non_blocking_read(cl_file, delimiter=b'\r\n\r\n')
            for line in header_line.decode('utf-8').strip().split('\r\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    headers[key] = value

            # Read POST data if Content-Length exists
            content_length = int(headers.get('Content-Length', 0))
            post_data = self.non_blocking_read(cl_file, size=content_length)
            print('POST Data:', post_data)

            # Handle server data
            sev_data = json.loads(post_data)
            response = {'status': 'success'}
            cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
            cl.send(json.dumps(response))
            cl.close()

            # {'requests': [{'ip': '192.168.65.200', 'data': {'group_id': 'STA-1', 'operation': 'remove-master'}}]}

            print(sev_data['requests'])
            if sev_data is not None:
                for req in sev_data['requests']:
                    oper_data = req['data']
                    handle_operation(oper_data,self.get_mac(),self.const,self.bin_const)
                machine.reset()
        except Exception as err:
            print(f"Error handling request: {err}")
            machine.reset()

    def non_blocking_read(self, file, delimiter=None, size=None):
        """Read data from file in a non-blocking way."""
        data = b''
        while (delimiter and delimiter not in data) or (size and len(data) < size):
            try:
                data += file.read(1)
            except OSError as e:
                if e.errno == 11:  # EAGAIN
                    time.sleep(0.1)
                else:
                    raise e
        return data

    def push_req(self):
        """Send a request to indicate availability to the server."""
        self.isAvail = True
        url = f"http://{self.server_ip}:5000/avail"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Successfully triggered queue processing.")
            else:
                print(f"Error: Received unexpected status code {response.status_code}")
        except Exception as err:
            print(f"An unexpected error occurred: {err}")

    def stop_req(self):
        """Send a request to stop availability."""
        self.isAvail = False
        url = f"http://{self.server_ip}:5000/stop"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Successfully stopped queue processing.")
            else:
                print(f"Error: Received unexpected status code {response.status_code}")
        except Exception as err:
            print(f"An unexpected error occurred: {err}")

    def process_notification_queue(self):
        """Process notifications and send them to the server."""
        notification_queue = QM_Object.read_notify_queue()
        response = None

        while notification_queue:
            notification = notification_queue.pop(0)
            api_url = f"http://{self.server_ip}:5000/click/update"
            try:
                response = requests.post(api_url, json=notification)
                if response.status_code == 200:
                    print("Server notified successfully")
                else:
                    print(f"Error notifying server: {response.status_code} - {response.text}")
            except Exception as err:
                print(f"Exception occurred while notifying server: {err}")
            finally:
                if response:
                    response.close()

        QM_Object.clear_notify_queue()
        # clear_notify_queue()

    




