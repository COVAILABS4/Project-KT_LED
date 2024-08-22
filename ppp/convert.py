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
        "rack_id": "R4",
        "mac": [44, 188, 187, 5, 54, 236],
        "bins": [
          {
            "color": [255, 255, 255],
            "led_pin": 12,
            "bin_id": "R4_01",
            "button_pin": 13,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [125, 169, 110]
              },
              {
                "enabled": true,
                "time": "14:37",
                "color": [201, 58, 51]
              },
              {
                "enabled": true,
                "time": "14:47",
                "color": [110, 234, 226]
              },
              {
                "enabled": true,
                "time": "14:54",
                "color": [237, 131, 214]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 25,
            "bin_id": "R4_02",
            "button_pin": 14,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [94, 70, 14]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [33, 20, 221]
              },
              {
                "enabled": true,
                "time": "14:52",
                "color": [123, 134, 207]
              },
              {
                "enabled": true,
                "time": "14:59",
                "color": [177, 238, 41]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 26,
            "bin_id": "R4_03",
            "button_pin": 15,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [115, 206, 143]
              },
              {
                "enabled": true,
                "time": "14:40",
                "color": [14, 248, 203]
              },
              {
                "enabled": true,
                "time": "14:47",
                "color": [105, 48, 189]
              },
              {
                "enabled": true,
                "time": "15:02",
                "color": [212, 191, 103]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 27,
            "bin_id": "R4_04",
            "button_pin": 16,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [230, 26, 9]
              },
              {
                "enabled": true,
                "time": "14:40",
                "color": [109, 167, 217]
              },
              {
                "enabled": true,
                "time": "14:47",
                "color": [116, 202, 217]
              },
              {
                "enabled": true,
                "time": "14:54",
                "color": [164, 99, 84]
              }
            ],
            "enabled": true,
            "clicked": false
          }
        ]
      },
      {
        "rack_id": "R2",
        "master": [44, 188, 187, 5, 54, 236],
        "mac": [44, 188, 187, 5, 52, 208],
        "bins": [
          {
            "color": [255, 255, 255],
            "led_pin": 12,
            "bin_id": "R2_01",
            "button_pin": 13,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [239, 222, 149]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [24, 64, 13]
              },
              {
                "enabled": true,
                "time": "14:52",
                "color": [226, 32, 40]
              },
              {
                "enabled": true,
                "time": "15:07",
                "color": [121, 191, 72]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 25,
            "bin_id": "R2_02",
            "button_pin": 14,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [39, 221, 211]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [80, 61, 182]
              },
              {
                "enabled": true,
                "time": "15:00",
                "color": [8, 63, 200]
              },
              {
                "enabled": true,
                "time": "15:10",
                "color": [74, 216, 47]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 26,
            "bin_id": "R2_03",
            "button_pin": 15,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [152, 154, 207]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [168, 192, 254]
              },
              {
                "enabled": true,
                "time": "14:52",
                "color": [150, 179, 92]
              },
              {
                "enabled": true,
                "time": "15:07",
                "color": [75, 15, 97]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 27,
            "bin_id": "R2_04",
            "button_pin": 16,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [156, 135, 16]
              },
              {
                "enabled": true,
                "time": "14:37",
                "color": [231, 42, 217]
              },
              {
                "enabled": true,
                "time": "14:47",
                "color": [250, 94, 157]
              },
              {
                "enabled": true,
                "time": "14:54",
                "color": [181, 5, 156]
              }
            ],
            "enabled": true,
            "clicked": false
          }
        ]
      },
      {
        "rack_id": "R3",
        "master": [44, 188, 187, 5, 54, 236],
        "mac": [44, 188, 187, 5, 33, 8],
        "bins": [
          {
            "color": [255, 255, 255],
            "led_pin": 12,
            "bin_id": "R3_01",
            "button_pin": 13,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [187, 249, 106]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [219, 160, 88]
              },
              {
                "enabled": true,
                "time": "15:00",
                "color": [195, 154, 55]
              },
              {
                "enabled": true,
                "time": "15:07",
                "color": [147, 156, 219]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 25,
            "bin_id": "R3_02",
            "button_pin": 14,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [11, 14, 98]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [241, 254, 154]
              },
              {
                "enabled": true,
                "time": "14:55",
                "color": [72, 73, 133]
              },
              {
                "enabled": true,
                "time": "15:02",
                "color": [138, 15, 110]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 26,
            "bin_id": "R3_03",
            "button_pin": 15,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [112, 248, 209]
              },
              {
                "enabled": true,
                "time": "14:37",
                "color": [39, 171, 46]
              },
              {
                "enabled": true,
                "time": "14:44",
                "color": [16, 8, 255]
              },
              {
                "enabled": true,
                "time": "14:51",
                "color": [199, 142, 84]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 27,
            "bin_id": "R3_04",
            "button_pin": 16,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [1, 94, 241]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [248, 66, 249]
              },
              {
                "enabled": true,
                "time": "15:00",
                "color": [5, 112, 243]
              },
              {
                "enabled": true,
                "time": "15:07",
                "color": [94, 49, 116]
              }
            ],
            "enabled": true,
            "clicked": false
          }
        ]
      },
      {
        "rack_id": "R6",
        "master": [44, 188, 187, 5, 54, 236],
        "mac": [44, 188, 187, 5, 62, 252],
        "bins": [
          {
            "color": [255, 255, 255],
            "led_pin": 12,
            "bin_id": "R6_01",
            "button_pin": 13,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [251, 76, 5]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [223, 127, 171]
              },
              {
                "enabled": true,
                "time": "15:00",
                "color": [129, 51, 240]
              },
              {
                "enabled": true,
                "time": "15:15",
                "color": [172, 37, 144]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 25,
            "bin_id": "R6_02",
            "button_pin": 14,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [118, 167, 8]
              },
              {
                "enabled": true,
                "time": "14:40",
                "color": [7, 201, 218]
              },
              {
                "enabled": true,
                "time": "14:55",
                "color": [72, 128, 121]
              },
              {
                "enabled": true,
                "time": "15:05",
                "color": [245, 5, 79]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 26,
            "bin_id": "R6_03",
            "button_pin": 15,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [82, 92, 225]
              },
              {
                "enabled": true,
                "time": "14:40",
                "color": [210, 174, 45]
              },
              {
                "enabled": true,
                "time": "14:55",
                "color": [24, 18, 78]
              },
              {
                "enabled": true,
                "time": "15:02",
                "color": [186, 76, 141]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 27,
            "bin_id": "R6_04",
            "button_pin": 16,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [60, 215, 28]
              },
              {
                "enabled": true,
                "time": "14:37",
                "color": [132, 92, 116]
              },
              {
                "enabled": true,
                "time": "14:47",
                "color": [201, 234, 225]
              },
              {
                "enabled": true,
                "time": "14:54",
                "color": [25, 97, 213]
              }
            ],
            "enabled": true,
            "clicked": false
          }
        ]
      },
      {
        "rack_id": "R7",
        "master": [44, 188, 187, 5, 54, 236],
        "mac": [44, 188, 187, 6, 42, 64],
        "bins": [
          {
            "color": [255, 255, 255],
            "led_pin": 12,
            "bin_id": "R7_01",
            "button_pin": 13,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [34, 60, 29]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [51, 89, 141]
              },
              {
                "enabled": true,
                "time": "15:00",
                "color": [243, 209, 104]
              },
              {
                "enabled": true,
                "time": "15:07",
                "color": [221, 5, 99]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 25,
            "bin_id": "R7_02",
            "button_pin": 14,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [208, 238, 233]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [236, 185, 191]
              },
              {
                "enabled": true,
                "time": "14:55",
                "color": [84, 42, 155]
              },
              {
                "enabled": true,
                "time": "15:05",
                "color": [3, 12, 112]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 26,
            "bin_id": "R7_03",
            "button_pin": 15,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [189, 109, 41]
              },
              {
                "enabled": true,
                "time": "14:40",
                "color": [180, 214, 75]
              },
              {
                "enabled": true,
                "time": "14:50",
                "color": [166, 225, 186]
              },
              {
                "enabled": true,
                "time": "15:00",
                "color": [89, 143, 201]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 27,
            "bin_id": "R7_04",
            "button_pin": 16,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [62, 250, 209]
              },
              {
                "enabled": true,
                "time": "14:40",
                "color": [48, 17, 134]
              },
              {
                "enabled": true,
                "time": "14:50",
                "color": [194, 210, 99]
              },
              {
                "enabled": true,
                "time": "15:05",
                "color": [160, 155, 117]
              }
            ],
            "enabled": true,
            "clicked": false
          }
        ]
      },
      {
        "rack_id": "R11",
        "master": [44, 188, 187, 5, 54, 236],
        "mac": [44, 188, 187, 5, 60, 196],
        "bins": [
          {
            "color": [255, 255, 255],
            "led_pin": 12,
            "bin_id": "R11_01",
            "button_pin": 13,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [5, 32, 96]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [206, 132, 195]
              },
              {
                "enabled": true,
                "time": "14:55",
                "color": [136, 107, 90]
              },
              {
                "enabled": true,
                "time": "15:05",
                "color": [54, 19, 81]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 25,
            "bin_id": "R11_02",
            "button_pin": 14,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [255, 201, 192]
              },
              {
                "enabled": true,
                "time": "14:45",
                "color": [217, 41, 224]
              },
              {
                "enabled": true,
                "time": "14:55",
                "color": [227, 161, 175]
              },
              {
                "enabled": true,
                "time": "15:02",
                "color": [11, 60, 248]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 26,
            "bin_id": "R11_03",
            "button_pin": 15,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [52, 231, 150]
              },
              {
                "enabled": true,
                "time": "14:40",
                "color": [92, 29, 196]
              },
              {
                "enabled": true,
                "time": "14:55",
                "color": [119, 139, 218]
              },
              {
                "enabled": true,
                "time": "15:02",
                "color": [57, 226, 189]
              }
            ],
            "enabled": true,
            "clicked": false
          },
          {
            "color": [255, 255, 255],
            "led_pin": 27,
            "bin_id": "R11_04",
            "button_pin": 16,
            "schedules": [
              {
                "enabled": true,
                "time": "14:30",
                "color": [202, 167, 24]
              },
              {
                "enabled": true,
                "time": "14:40",
                "color": [138, 40, 111]
              },
              {
                "enabled": true,
                "time": "14:50",
                "color": [135, 194, 69]
              },
              {
                "enabled": true,
                "time": "15:00",
                "color": [239, 169, 63]
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