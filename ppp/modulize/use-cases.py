from config import Config  # Import the Config class from config.py
  # Set the correct path to your JSON file

# Create an instance of the Config class
config = Config()

# Fetch all data from the config file
config_data = config.read_config()
print("All Config Data:", config_data)

# Fetch the value of a specific key ("PASSWORD")
specific_value = config.read_config("SSID")
print("Password:", specific_value)

#-----------------------Constant.py

from Constants import Constants

# Create an instance of Constants
config = Constants()

# Access the I2C instance
i2c = config.get_i2c()
rtc = config.get_rtc()
buzzer = config.get_buzzer()
relay = config.get_relay()

# Print current active bins
print("Active Bins:", config.get_active_bins())

# Set and get values
config.set_current_group_id(1)
config.set_current_rack("Rack1")
config.add_active_bin("Bin1")

print("Current Group ID:", config.get_current_group_id())
print("Current Rack:", config.get_current_rack())
print("Active Bins:", config.get_active_bins())

#------------------------------QUEUE

from QueueManager import QueueManager

def main():
    # Create an instance of QueueManager
    queue_manager = QueueManager()

    # Add items to the notification and message queues
    queue_manager.add_notify_queue({'id': 1, 'message': 'New notification!'})
    queue_manager.add_message_queue({'id': 1, 'message': 'New message!'})

    # Read and print the current queues
    print("Notification Queue:", queue_manager.read_notify_queue())
    print("Message Queue:", queue_manager.read_message_queue())

    # Clear the queues
    queue_manager.clear_notify_queue()
    queue_manager.clear_message_queue()

    # Print the queues after clearing
    print("Notification Queue after clearing:", queue_manager.read_notify_queue())
    print("Message Queue after clearing:", queue_manager.read_message_queue())

if __name__ == "__main__":
    main()




#---------Station Mode

# Example usage
station = Station(ssid="Your_SSID", password="Your_PASSWORD", static_ip="100", server_no="5000")
station.connect_to_wifi()
station.start_server()




# Example usage
if __name__ == "__main__":
    esp_now_manager = ESPNowManager()
    print("Switch OFF - Offline State")
    time.sleep(2)
    esp_now_manager.disconnect_wifi()
    print("Switch OFF")
    time.sleep(2)
    esp_now_manager.init_esp_now()
    time.sleep(2)
    esp_now_manager.sent_time()
    time.sleep(2)
    esp_now_manager.notify_slave("avail")
    time.sleep(20)
