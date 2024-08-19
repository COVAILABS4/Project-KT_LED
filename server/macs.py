import network

# Initialize the WiFi interface in station mode
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Get the MAC address in byte format
mac_address_bytes = wlan.config('mac')

print([i for i in mac_address_bytes])

print('MAC Address in bytes:', mac_address_bytes)
