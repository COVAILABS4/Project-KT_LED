import json

# Function to normalize color values from range 0-255 to 0-64
def normalize_color(value):
    return int((value / 255) * 64)

# Function to process JSON data from a string
def process_json_string(json_string):
    datas = json.loads(json_string)
    
    # Iterate through the bins and their schedules
    for data in datas:
        for bin in data.get('bins', []):
            for schedule in bin.get('schedules', []):
                # Normalize the color values
                schedule['color'] = [normalize_color(c) for c in schedule['color']]
            # Normalize the bin color
            bin['color'] = [0,0,0]
    
    # Convert processed data back to JSON string
    return datas

# Example input JSON string
input_json_string = '''
 [
      {
        "rack_id": "R1",
        "mac": [
          44,
          188,
          187,
          5,
          54,
          236
        ],
        "device_id": "KT-4",
        "bins": [
          {
            "color": [
              255,
              255,
              255
            ],
            "led_pin": 12,
            "bin_id": "R1_01",
            "button_pin": 13,
            "schedules": [
              {
                "time": "16:20",
                "enabled": true,
                "color": [
                  255,
                  0,
                  0
                ]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [
              255,
              255,
              255
            ],
            "led_pin": 25,
            "bin_id": "R1_02",
            "button_pin": 14,
            "schedules": [
              {
                "time": "16:23",
                "enabled": true,
                "color": [
                  0,
                  0,
                  255
                ]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [
              255,
              255,
              255
            ],
            "led_pin": 26,
            "bin_id": "R1_03",
            "button_pin": 15,
            "schedules": [
              {
                "time": "16:23",
                "enabled": true,
                "color": [
                  255,
                  0,
                  255
                ]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [
              255,
              255,
              255
            ],
            "led_pin": 27,
            "bin_id": "R1_04",
            "button_pin": 16,
            "schedules": [],
            "enabled": true,
            "clicked": false
          }
        ]
      },
      {
        "rack_id": "R2",
        "master": [
          44,
          188,
          187,
          5,
          54,
          236
        ],
        "mac": [
          44,
          188,
          187,
          6,
          42,
          64
        ],
        "device_id": "KT-7",
        "bins": [
          {
            "color": [
              255,
              255,
              255
            ],
            "led_pin": 12,
            "bin_id": "R2_01",
            "button_pin": 13,
            "schedules": [
              {
                "time": "10:12",
                "enabled": true,
                "color": [
                  255,
                  0,
                  255
                ]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [
              255,
              255,
              255
            ],
            "led_pin": 25,
            "bin_id": "R2_02",
            "button_pin": 14,
            "schedules": [
              {
                "time": "10:12",
                "enabled": true,
                "color": [
                  0,
                  0,
                  255
                ]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [
              255,
              255,
              255
            ],
            "led_pin": 26,
            "bin_id": "R2_03",
            "button_pin": 15,
            "schedules": [],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [
              255,
              255,
              255
            ],
            "led_pin": 27,
            "bin_id": "R2_04",
            "button_pin": 16,
            "schedules": [
              {
                "time": "10:12",
                "enabled": true,
                "color": [
                  255,
                  255,
                  0
                ]
              }
            ],
            "enabled": true,
            "clicked": false
          }
        ]
      }
    ]
'''

# Process the input JSON string
normalized_json_string = process_json_string(input_json_string)

with open('res.json', 'w') as f:
    json.dump(normalized_json_string, f)