import json
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# Configuration files
CONFIG_FILE = "config.json"
SCHEDULE_FILE = "data.json"

# Default configuration
DEFAULT_CONFIG = {
    "SSID": "KT-AP",
    "PASSWORD": "1234567890",
    "KIT_NO": "1",
    "STATIC_NO": "1",
}

DEFAULT_SCHEDULE = []

# Predefined color options (8 colors) - now in RGB format [R, G, B]
COLOR_OPTIONS = [
    {"name": "White", "value": [255, 255, 255]},
    {"name": "Red", "value": [255, 0, 0]},
    {"name": "Green", "value": [0, 255, 0]},
    {"name": "Blue", "value": [0, 0, 255]},
    {"name": "Yellow", "value": [255, 255, 0]},
    {"name": "Cyan", "value": [0, 255, 255]},
    {"name": "Magenta", "value": [255, 0, 255]},
    {"name": "Orange", "value": [255, 165, 0]},
]

# Initialize files if they don't exist
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f)

if not os.path.exists(SCHEDULE_FILE):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(DEFAULT_SCHEDULE, f)

# HTML Templates
MAIN_MENU = """
"""


AP_SETUP_TEMPLATE = """
"""

SCHEDULE_SETUP_TEMPLATE = """
"""


# Read HTML content from main.txt
with open("main.txt", "r", encoding="utf-8") as file:
    MAIN_MENU = file.read()

with open("ap.txt", "r", encoding="utf-8") as file:
    AP_SETUP_TEMPLATE = file.read()

with open("sch.txt", "r", encoding="utf-8") as file:
    SCHEDULE_SETUP_TEMPLATE = file.read()


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(MAIN_MENU.encode())

        elif path == "/setup-ap":
            config = self.get_config()
            html = AP_SETUP_TEMPLATE.format(
                ssid=config["SSID"],
                password=config["PASSWORD"],
                kit_no=config["KIT_NO"],
                static_no=config["STATIC_NO"],
            )
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())

        elif path == "/setup-schedule":
            schedule = self.get_schedule()
            all_enabled = (
                all(item["enabled"] for item in schedule) if schedule else False
            )

            color_options_html = ""
            for color in COLOR_OPTIONS:
                # Convert RGB to hex for display
                hex_color = "#{:02x}{:02x}{:02x}".format(*color["value"])
                color_options_html += f"""
                <div class="color-option" 
                     style="background-color: {hex_color}"
                     onclick="selectColor(this, '{color['value'][0]},{color['value'][1]},{color['value'][2]}')"></div>
                """

            html = SCHEDULE_SETUP_TEMPLATE.format(
                schedule_entries=self.generate_schedule_entries(schedule),
                toggle_all_text="Disable All" if all_enabled else "Enable All",
                color_options=color_options_html,
            )
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())

        elif path.startswith("/delete-schedule/"):
            index = int(path.split("/")[-1])
            schedule = self.get_schedule()
            if 0 <= index < len(schedule):
                schedule.pop(index)
                self.save_schedule(schedule)
            self.send_response(303)
            self.send_header("Location", "/setup-schedule")
            self.end_headers()

        elif path.startswith("/toggle-schedule/"):
            index = int(path.split("/")[-1])
            schedule = self.get_schedule()
            if 0 <= index < len(schedule):
                schedule[index]["enabled"] = not schedule[index]["enabled"]
                self.save_schedule(schedule)
            self.send_response(303)
            self.send_header("Location", "/setup-schedule")
            self.end_headers()

        elif path == "/enable-all":
            schedule = self.get_schedule()
            for item in schedule:
                item["enabled"] = True
            self.save_schedule(schedule)
            self.send_response(303)
            self.send_header("Location", "/setup-schedule")
            self.end_headers()

        elif path == "/disable-all":
            schedule = self.get_schedule()
            for item in schedule:
                item["enabled"] = False
            self.save_schedule(schedule)
            self.send_response(303)
            self.send_header("Location", "/setup-schedule")
            self.end_headers()

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")
        post_params = parse_qs(post_data)

        if self.path == "/save-ap":
            config = {
                "SSID": post_params["ssid"][0],
                "PASSWORD": post_params["password"][0],
                "KIT_NO": post_params["kit_no"][0],
                "STATIC_NO": post_params["static_no"][0],
            }
            self.save_config(config)
            self.send_response(303)
            self.send_header("Location", "/setup-ap")
            self.end_headers()

        elif self.path == "/add-schedule":
            schedule = self.get_schedule()
            enabled = "enabled" in post_params

            # Parse color and normalize to 0-65
            color_parts = post_params["color"][0].split(",")
            if len(color_parts) == 3:
                r, g, b = map(int, color_parts)
                # Normalize to 0-65 (rounding to nearest integer)
                r_norm = round((r / 255) * 65)
                g_norm = round((g / 255) * 65)
                b_norm = round((b / 255) * 65)
                color = [r_norm, g_norm, b_norm]
            else:
                color = [65, 65, 65]  # Default to white if parsing fails

            schedule.append(
                {
                    "time": post_params["time"][0],
                    "color": color,
                    "enabled": enabled,
                }
            )
            self.save_schedule(schedule)
            self.send_response(303)
            self.send_header("Location", "/setup-schedule")
            self.end_headers()

    def get_config(self):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    def save_config(self, config):
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def get_schedule(self):
        with open(SCHEDULE_FILE, "r") as f:
            schedule = json.load(f)
            schedule.sort(key=lambda x: x["time"])
            return schedule

    def save_schedule(self, schedule):
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(schedule, f)

    def generate_schedule_entries(self, schedule):
        entries = []

        for i, item in enumerate(schedule, start=1):
            # Denormalize color from 0–65 to 0–255
            if isinstance(item["color"], list) and len(item["color"]) == 3:
                r, g, b = item["color"]
                r_denorm = round((r / 65) * 255)
                g_denorm = round((g / 65) * 255)
                b_denorm = round((b / 65) * 255)
                hex_color = "#{:02x}{:02x}{:02x}".format(r_denorm, g_denorm, b_denorm)
            else:
                hex_color = "#FFFFFF"  # fallback to white

            status_text = "Enabled" if item["enabled"] else "Disabled"
            status_class = "status-enabled" if item["enabled"] else "status-disabled"
            toggle_text = "Disable" if item["enabled"] else "Enable"

            entries.append(
                f"""
                <tr>
                    <td>{i}</td>
                    <td>{item['time']}</td>
                    <td>
                        <div class="color-box" style="background-color:{hex_color};"></div>
                    </td>
                    <td class="{status_class}">{status_text}</td>
                    <td>
                        <div class="action-btns">
                            <form style="display:inline;" action="/toggle-schedule/{i - 1}" method="get">
                                <button type="submit" class="action-button toggle-button">{toggle_text}</button>
                            </form>
                            <form style="display:inline;" action="/delete-schedule/{i - 1}" method="get">
                                <button type="submit" class="action-button delete-button">Delete</button>
                            </form>
                        </div>
                    </td>
                </tr>
                """
            )

        return "".join(entries)


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
