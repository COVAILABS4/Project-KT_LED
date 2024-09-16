import ujson

config_file_path = '/config.json'

class Config():
    def __init__(self):
        self.KIT_NO = 1
        self.STATIC_IP = 1
        self.SERVER_NO = 255
        self.SSID = 'ACTFIBERNET'
        self.PASSWORD = 'act12345'

    def read_config(self, key=None):

        try:
            with open(config_file_path, 'r') as file:
                config = ujson.load(file)
                
                # If a key is provided, return the key's value, else return the entire config
                if key:
                    return config.get(key, None)  # Return None if key does not exist
                return config  # Return entire config if no key is specified
        except OSError:
            # If file does not exist, return an empty dictionary
            return {}
