# QueueManager.py

import ujson

class QueueManager:
    def __init__(self, file_path='queue.json'):
        self.file_path = file_path

    def _read_json(self):
        """Reads JSON data from the file."""
        try:
            with open(self.file_path, 'r') as file:
                data = ujson.load(file)
                return data
        except Exception as e:
            print(f"Error reading {self.file_path}: {e}")
            return None

    def _write_json(self, data):
        """Writes JSON data to the file."""
        try:
            with open(self.file_path, 'w') as file:
                ujson.dump(data, file)
        except Exception as e:
            print(f"Error writing to {self.file_path}: {e}")

    def read_notify_queue(self):
        """Reads and returns the notification queue."""
        data = self._read_json()
        if data is not None:
            return data.get('notification_queue', [])
        return []

    def add_notify_queue(self, item):
        """Adds an item to the notification queue."""
        data = self._read_json()
        if data is not None:
            if 'notification_queue' not in data:
                data['notification_queue'] = []
            data['notification_queue'].append(item)
            self._write_json(data)

    def clear_notify_queue(self):
        """Clears the notification queue."""
        data = self._read_json()
        if data is not None:
            data['notification_queue'] = []
            self._write_json(data)

    def read_message_queue(self):
        """Reads and returns the message queue."""
        data = self._read_json()
        if data is not None:
            return data.get('message_queue', [])
        return []

    def add_message_queue(self, item):
        """Adds an item to the message queue."""
        data = self._read_json()
        if data is not None:
            if 'message_queue' not in data:
                data['message_queue'] = []
            data['message_queue'].append(item)
            self._write_json(data)

    def clear_message_queue(self):
        """Clears the message queue."""
        data = self._read_json()
        if data is not None:
            data['message_queue'] = []
            self._write_json(data)
