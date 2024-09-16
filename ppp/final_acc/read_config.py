import ujson
KIT_NO = 1

STATIC_IP = 1


SERVER_NO = 255

SSID = 'ACTFIBERNET'
PASSWORD = 'act12345'



# Define file path
config_file_path = '/config.json'

def read_config(file_path):
    """Reads JSON configuration from the specified file."""
    try:
        with open(file_path, 'r') as file:
            config = ujson.load(file)
            return config
    except OSError:
        # If file does not exist, return an empty dictionary
        return {}

# Read existing configuration
Local = read_config(config_file_path)

# Store configuration values in variables
KIT_NO = Local.get("KIT_NO", "")
STATIC_IP = Local.get("STATIC_NO", "")

if STATIC_IP=="":
    STATIC_IP = KIT_NO


SERVER_NO = Local.get("SERVER_NO", 0)
SSID = Local.get("SSID", "")
PASSWORD = Local.get("PASSWORD", "")

# Print variables
print("KIT_NO =", KIT_NO)
print("STATIC_NO =", STATIC_IP)
print("SERVER_NO =", SERVER_NO)
print("SSID =", SSID)
print("PASSWORD =", PASSWORD)

