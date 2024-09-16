import network
import espnow
import machine
import _thread
import time
from ubinascii import hexlify
from file_operations import update_data_json_from_message, get_data
# Assuming read_message_queue and clear_message_queue are imported
from QueueManager import QueueManager

QObject = QueueManager()

class ESPNowManager:
    def __init__(self, const, bin_const):
        self.e = None
        self.receive_thread = None
        self.stop_thread_flag = False
        self.const = const
        self.bin_const = bin_const
        self.rtc = const.get_rtc()

    def start_sta(self):
        self.sta = network.WLAN(network.STA_IF)
        self.sta.active(True)

    def init_esp_now(self):
        print("Initialize the ESPNOW")
        try:
            self.start_sta()
            self.e = espnow.ESPNow()
            self.e.active(True)
        except Exception:
            machine.reset()

        

        try:
            _thread.start_new_thread(self.receive_message, (self.e,))
            print(_thread.stack_size())
        except Exception as err:
            print(f"Error starting thread 1: {err}")
            machine.reset()

    def close_esp_now(self):
        self.e.active(False)
        self.sta.active(False)
        print("ESPNOW Closed")

    def sent_time(self):
        print("NOTICED")
        data = get_data()
        for rack in data[0]['racks'][1:]:
            rc_mac = bytes(rack['mac'])
            rtc_time = self.rtc.get_time()
            time_str = f"{rtc_time[3]}:{rtc_time[4]}:{rtc_time[5]}:999999".encode()
            try:
                self.e.add_peer(rc_mac)
            except Exception:
                pass
            self.e.send(rc_mac, time_str)

    def notify_slave(self, message):
        data = get_data()
        print()
        for rack in data[0]['racks'][1:]:
            rc_mac = bytes(rack['mac'])
            try:
                self.e.add_peer(rc_mac)
            except Exception:
                print("Already")
            print(rc_mac, message)
            try:
                self.e.send(rc_mac, message)
            except Exception:
                print("Arises")
            # time.sleep(4)
            print("Notified")

    def stop_thread(self):
        self.stop_thread_flag = True

    def receive_message(self, e):
        while True:
            host, msg = e.recv()
            if msg:
                
                print(f"Received from {hexlify(host).decode()}: {msg}")

                print(self.const._current_group_id)

                update_data_json_from_message(msg, const= self.const,bin_const=self.bin_const)
            time.sleep(1)

    def process_message_queue(self):
        """Process messages from the message queue and send them via ESPNOW."""
        message_queue = QObject.read_message_queue()  # Fetch the message queue

        for item in message_queue:
            mac, msg = tuple(item)
            mac = bytes(mac)
            try:
                try:
                    self.e.add_peer(mac)
                except Exception:
                    pass
                self.e.send(mac, msg)
                print(f"Sent to {mac}: {msg}")
                time.sleep(0.5)  # Adding a small delay between sending messages
            except Exception as err:
                print(f"Error sending message to {mac}: {err}")

        QObject.clear_message_queue()  # Clear the queue after processing
