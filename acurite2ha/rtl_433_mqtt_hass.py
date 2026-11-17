#!/usr/bin/env python3
# coding=utf-8

"""MQTT Home Assistant auto discovery for rtl_433 events."""

# It is strongly recommended to run rtl_433 with "-C si" and "-M newmodel".

# Needs Paho-MQTT https://pypi.python.org/pypi/paho-mqtt

# Option: PEP 3143 - Standard daemon process library
# (use Python 3.x or pip install python-daemon)
# import daemon

from __future__ import print_function, with_statement

import json
import os
import time
import paho.mqtt.client as mqtt
import logging
from datetime import datetime

MQTT_HOST = os.environ['MQTT_HOST']
MQTT_PORT = os.environ['MQTT_PORT']
MQTT_USERNAME = os.environ['MQTT_USERNAME']
MQTT_PASSWORD = os.environ['MQTT_PASSWORD']
MQTT_TOPIC = os.environ['MQTT_TOPIC']
DISCOVERY_PREFIX = os.environ['DISCOVERY_PREFIX']
WHITELIST_ENABLE = os.environ['WHITELIST_ENABLE']
WHITELIST = os.environ['WHITELIST']
DISCOVERY_INTERVAL = os.environ['DISCOVERY_INTERVAL']
AUTO_DISCOVERY = os.environ['AUTO_DISCOVERY']
DEBUG = os.environ['DEBUG']
EXPIRE_AFTER = os.environ['EXPIRE_AFTER']
#MQTT_RETAIN = os.environ['MQTT_RETAIN']
# Convert number environment variables to int
MQTT_PORT = int(MQTT_PORT)
DISCOVERY_INTERVAL = int(DISCOVERY_INTERVAL)
# Make sure EXPIRE_AFTER is an integer
EXPIRE_AFTER = int(EXPIRE_AFTER)


discovery_timeouts = {}

whitelist_list = WHITELIST.split()
blocked = []
rate_limited = {}

if DEBUG == "true":
    LOGLEVEL = os.environ.get('LOGLEVEL', 'DEBUG').upper()
else:
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()

if WHITELIST_ENABLE == "true":
    whitelist_on = True
else:
    whitelist_on = False

if AUTO_DISCOVERY == "true":
    auto_discovery  = True
else:
    auto_discovery  = False

mappings = {
    "time": {
        "device_type": "sensor",
        "object_suffix": "last_seen",
        "config": {
            "name": "Last Seen",
            "device_class": "timestamp",
            "entity_category": "diagnostic",
            "value_template": "{{ value }}"
        }
    },
    "protocol": {
        "device_type": "sensor",
        "object_suffix": "protocol",
        "config": {
            "name": "Protocol",
            "entity_category": "diagnostic",
            "value_template": "{{ value }}"
        }
    },
    "sequence_num": {
        "device_type": "sensor",
        "object_suffix": "sequence",
        "config": {
            "name": "Sequence Number",
            "entity_category": "diagnostic",
            "value_template": "{{ value }}"
        }
    },
    "message_type": {
        "device_type": "sensor",
        "object_suffix": "msg_type",
        "config": {
            "name": "Message Type",
            "entity_category": "diagnostic",
            "value_template": "{{ value }}"
        }
    },
    "mod": {
        "device_type": "sensor",
        "object_suffix": "modulation",
        "config": {
            "name": "Modulation",
            "entity_category": "diagnostic",
            "value_template": "{{ value }}"
        }
    },
    "freq": {
        "device_type": "sensor",
        "object_suffix": "freq",
        "config": {
            "name": "Frequency",
            "device_class": "frequency",
            "unit_of_measurement": "MHz",
            "entity_category": "diagnostic",
            "value_template": "{{ value }}"
        }
    },
    "channel": {
        "device_type": "sensor",
        "object_suffix": "channel",
        "config": {
            "name": "Device Channel",
            "device_class": "enum",
            "options": ["A", "B", "C"],
            "entity_category": "diagnostic",
            "value_template": "{{ value }}"
        }
    },
    "temperature_C": {
        "device_type": "sensor",
        "object_suffix": "T",
        "config": {
            "name": "Temperature",
            "device_class": "temperature",
            "state_class":"measurement",
            "unit_of_measurement": "°C",
            "value_template": "{{ value|float }}"
        }
    },
    "temperature_1_C": {
        "device_type": "sensor",
        "object_suffix": "T1",
        "config": {
            "name": "Temperature 1",
            "device_class": "temperature",
            "state_class":"measurement",
            "unit_of_measurement": "°C",
            "value_template": "{{ value|float }}"
        }
    },
    "temperature_2_C": {
        "device_type": "sensor",
        "object_suffix": "T2",
        "config": {
            "name": "Temperature 2",
            "device_class": "temperature",
            "state_class":"measurement",
            "unit_of_measurement": "°C",
            "value_template": "{{ value|float }}"
        }
    },
    "temperature_F": {
        "device_type": "sensor",
        "object_suffix": "T",
        "config": {
            "name": "Temperature",
            "device_class": "temperature",
            "state_class":"measurement",
            "unit_of_measurement": "°F",
            "value_template": "{{ value|float }}"
        }
    },
    "temperature_1_F": {
        "device_type": "sensor",
        "object_suffix": "T1",
        "config": {
            "name": "Temperature 1",
            "device_class": "temperature",
            "state_class":"measurement",
            "unit_of_measurement": "°F",
            "value_template": "{{ value|float }}"
        }
    },
    "temperature_2_F": {
        "device_type": "sensor",
        "object_suffix": "T2",
        "config": {
            "name": "Temperature 2",
            "device_class": "temperature",
            "state_class":"measurement",
            "unit_of_measurement": "°F",
            "value_template": "{{ value|float }}"
        }
    },

    "battery_ok": {
        "device_type": "sensor",
        "object_suffix": "B",
        "config": {
            "name": "Battery",
            "device_class": "battery",
            "state_class": "measurement",
            "unit_of_measurement": "%",
            "entity_category": "diagnostic",
            "value_template": "{{ (float(value) * 99 + 1) | int }}"
        }
    },

    "humidity": {
        "device_type": "sensor",
        "object_suffix": "H",
        "config": {
            "name": "Humidity",
            "device_class": "humidity",
            "state_class":"measurement",
            "unit_of_measurement": "%",
            "value_template": "{{ value|float }}"
        }
    },

    "moisture": {
        "device_type": "sensor",
        "object_suffix": "M",
        "config": {
            "name": "Moisture",
            "device_class": "moisture",
            "state_class":"measurement",
            "unit_of_measurement": "%",
            "value_template": "{{ value|float }}"
        }
    },

    "pressure_hPa": {
        "device_type": "sensor",
        "object_suffix": "P",
        "config": {
            "name": "Pressure",
            "device_class": "pressure",
            "state_class":"measurement",
            "unit_of_measurement": "hPa",
            "value_template": "{{ value|float }}"
        }
    },

    "pressure_kPa": {
        "device_type": "sensor",
        "object_suffix": "P",
        "config": {
            "name": "Pressure",
            "device_class": "pressure",
            "state_class":"measurement",
            "unit_of_measurement": "kPa",
            "value_template": "{{ value|float }}"
        }
    },
    
    "pressure_inHg": {
        "device_type": "sensor",
        "object_suffix": "P",
        "config": {
            "name": "Pressure",
            "device_class": "pressure",
            "state_class":"measurement",
            "unit_of_measurement": "inHg",
            "value_template": "{{ value|float }}"
        }
    },

    "wind_speed_km_h": {
        "device_type": "sensor",
        "object_suffix": "WS",
        "config": {
            "name": "Wind Speed",
            "device_class": "wind_speed",
            "state_class":"measurement",
            "unit_of_measurement": "km/h",
            "value_template": "{{ value|float }}"
        }
    },

    "wind_avg_km_h": {
        "device_type": "sensor",
        "object_suffix": "WS",
        "config": {
            "name": "Wind Speed",
            "device_class": "wind_speed",
            "state_class": "measurement",
            "unit_of_measurement": "km/h",
            "value_template": "{{ value|float }}"
        }
    },

    "wind_avg_mi_h": {
        "device_type": "sensor",
        "object_suffix": "WS",
        "config": {
            "name": "Wind Speed",
            "device_class": "wind_speed",
            "state_class": "measurement",
            "unit_of_measurement": "mph",
            "value_template": "{{ value|float }}"
        }
    },

    "wind_avg_m_s": {
        "device_type": "sensor",
        "object_suffix": "WS",
        "config": {
            "name": "Wind Average",
            "device_class": "wind_speed",
            "state_class":"measurement",
            "unit_of_measurement": "m/s",
            "value_template": "{{ value|float }}",
        }
    },

    "wind_speed_m_s": {
        "device_type": "sensor",
        "object_suffix": "WS",
        "config": {
            "name": "Wind Speed",
            "device_class": "wind_speed",
            "state_class":"measurement",
            "unit_of_measurement": "m/s",
            "value_template": "{{ value|float }}",
        }
    },

    "gust_speed_km_h": {
        "device_type": "sensor",
        "object_suffix": "GS",
        "config": {
            "name": "Gust Speed",
            "device_class": "wind_speed",
            "state_class":"measurement",
            "unit_of_measurement": "km/h",
            "value_template": "{{ value|float }}"
        }
    },

    "wind_max_km_h": {
        "device_type": "sensor",
        "object_suffix": "GS",
        "config": {
            "name": "Wind Max",
            "device_class": "wind_speed",
            "state_class":"measurement",
            "unit_of_measurement": "km/h",
            "value_template": "{{ value|float }}"
        }
    },

    "wind_max_m_s": {
        "device_type": "sensor",
        "object_suffix": "GS",
        "config": {
            "name": "Wind Max",
            "device_class": "wind_speed",
            "state_class":"measurement",
            "unit_of_measurement": "m/s",
            "value_template": "{{ value|float }}",
        }
    },

    "gust_speed_m_s": {
        "device_type": "sensor",
        "object_suffix": "GS",
        "config": {
            "name": "Gust Speed",
            "device_class": "wind_speed",
            "state_class":"measurement",
            "unit_of_measurement": "m/s",
            "value_template": "{{ value|float }}",
        }
    },

    "wind_dir_deg": {
        "device_type": "sensor",
        "object_suffix": "WD",
        "config": {
            "name": "Wind Direction",
            "device_class": "wind_direction",
            "state_class": "measurement_angle",
            "unit_of_measurement": "°",
            "value_template": "{{ value|float }}"
        }
    },

    "rain_mm": {
        "device_type": "sensor",
        "object_suffix": "RT",
        "config": {
            "name": "Rain Total",
            "device_class": "precipitation",
            "state_class":"total_increasing",
            "unit_of_measurement": "mm",
            "value_template": "{{ value|float }}"
        }
    },

    "rain_mm_h": {
        "device_type": "sensor",
        "object_suffix": "RR",
        "config": {
            "name": "Rain Rate",
            "device_class": "precipitation_intensity",
            "state_class":"measurement",
            "unit_of_measurement": "mm/h",
            "value_template": "{{ value|float }}"
        }
    },

    "rain_in": {
        "device_type": "sensor",
        "object_suffix": "RT",
        "config": {
            "name": "Rain Total",
            "device_class": "precipitation",
            "state_class":"total_increasing",
            "unit_of_measurement": "in",
            "value_template": "{{ value|float }}"
        }
    },

    "rain_rate_in_h": {
        "device_type": "sensor",
        "object_suffix": "RR",
        "config": {
            "name": "Rain Rate",
            "device_class": "precipitation_intensity",
            "state_class":"measurement",
            "unit_of_measurement": "in/h",
            "value_template": "{{ value|float }}"
        }
    },

    "tamper": {
        "device_type": "binary_sensor",
        "object_suffix": "tamper",
        "config": {
            "name": "Tamper",
            "device_class": "safety",
            "force_update": True,
            "payload_on": "1",
            "payload_off": "0"
        }
    },

    "alarm": {
        "device_type": "binary_sensor",
        "object_suffix": "alarm",
        "config": {
            "name": "Alarm",
            "device_class": "safety",
            "force_update": True,
            "payload_on": "1",
            "payload_off": "0"
        }
    },

    "rssi": {
        "device_type": "sensor",
        "object_suffix": "rssi",
        "config": {
            "name": "RSSI",
            "device_class": "signal_strength",
            "state_class":"measurement",
            "unit_of_measurement": "dB",
            "entity_category": "diagnostic",
            "value_template": "{{ value|float }}"
        }
    },

    "snr": {
        "device_type": "sensor",
        "object_suffix": "snr",
        "config": {
            "name": "SNR",
            "device_class": "signal_strength",
            "state_class":"measurement",
            "unit_of_measurement": "dB",
            "entity_category": "diagnostic",
            "value_template": "{{ value|float }}"
        }
    },

    "noise": {
        "device_type": "sensor",
        "object_suffix": "noise",
        "config": {
            "name": "Signal Noise",
            "device_class": "signal_strength",
            "state_class":"measurement",
            "unit_of_measurement": "dB",
            "entity_category": "diagnostic",
            "value_template": "{{ value|float }}"
        }
    },

    "depth_cm": {
        "device_type": "sensor",
        "object_suffix": "D",
        "config": {
            "name": "Depth",
            "device_class": "distance",
            "state_class":"measurement",
            "unit_of_measurement": "cm",
            "value_template": "{{ value|float }}"
        }
    },

    "power_W": {
        "device_type": "sensor",
        "object_suffix": "watts",
        "config": {
            "name": "Power",
            "device_class": "power",
            "state_class":"measurement",
            "unit_of_measurement": "W",
            "value_template": "{{ value|float }}"
        }
    },

    "lux": {
        "device_type": "sensor",
        "object_suffix": "lux",
        "config": {
            "name": "Outside Illuminance",
            "device_class": "illuminance",
            "state_class":"measurement",
            "unit_of_measurement": "lx",
            "value_template": "{{ value|float }}"
        }
    },

    "light_klx": {
        "device_type": "sensor",
        "object_suffix": "light_klx",
        "config": {
            "name": "Outside Illuminance",
            "device_class": "illuminance",
            "state_class": "measurement",
            "unit_of_measurement": "lx",
            "value_template": "{{ (value|float * 1000)|round(0)|int }}"
        }
    },

    "brightness": {
        "device_type": "sensor",
        "object_suffix": "bri",
        "config": {
            "name": "Brightness",
            "device_class": "illuminance",
            "state_class":"measurement",
            "unit_of_measurement": "lx",
            "value_template": "{{ value|float }}"
        }
    },

    "uv": {
        "device_type": "sensor",
        "object_suffix": "uv",
        "config": {
            "name": "UV Index",
            "state_class":"measurement",
            "unit_of_measurement": "UV Index",
            "value_template": "{{ value|int }}"
        }
    },

    "storm_dist": {
        "device_type": "sensor",
        "object_suffix": "stdist",
        "config": {
            "name": "Lightning Distance",
            "device_class":"distance",
            "state_class":"measurement",
            "unit_of_measurement": "mi",
            "value_template": "{{ value|float }}"
        }
    },

    "strike_distance": {
        "device_type": "sensor",
        "object_suffix": "stdist",
        "config": {
            "name": "Lightning Distance",
            "device_class":"distance",
            "state_class":"measurement",
            "unit_of_measurement": "mi",
            "value_template": "{{ value|float }}"
        }
    
    },
    "consumption": {
        "device_type": "sensor",
        "object_suffix": "meter",
        "config": {
            "name": "Meter",
            "device_class": "gas",
            "state_class":"total_increasing",
            "unit_of_measurement": "ft³",
            "value_template": "{{ value|float }}"
        }
    },
    "strike_count": {
        "device_type": "sensor",
        "object_suffix": "strcnt",
        "config": {
            "name": "Lightning Strike Count",
            "state_class":"total_increasing",
            "unit_of_measurement": "strikes",
            "value_template": "{{ value|int }}"
        }
    },
    "active": {
        "device_type": "binary_sensor",
        "object_suffix": "active",
        "config": {
            "name": "Active",
            "device_class": "running",
            "entity_category": "diagnostic",
            "payload_on": "1",
            "payload_off": "0"
        }
    },
    "rfi": {
        "device_type": "binary_sensor",
        "object_suffix": "rfi",
        "config": {
            "name": "Interference",
            "device_class": "problem",
            "entity_category": "diagnostic",
            "payload_on": "1",
            "payload_off": "0"
        }
    },
    "exception": {
        "device_type": "sensor",
        "object_suffix": "exception",
        "config": {
            "name": "Exception",
            "entity_category": "diagnostic",
            "value_template": "{{ value }}"
        }
    },
    "raw_msg": {
        "device_type": "sensor",
        "object_suffix": "raw_msg",
        "config": {
            "name": "Raw Message",
            "entity_category": "diagnostic",
            "value_template": "{{ value }}"
        }
    }
}


def mqtt_connect(client, userdata, flags, rc):
    """Callback for MQTT connects."""
    print("MQTT connected: " + mqtt.connack_string(rc))
    client.publish("/".join([MQTT_TOPIC, "status"]), payload="online", qos=0, retain=True)
    if rc != 0:
        logging.critical("Could not connect. Error: " + str(rc))
    else:
        client.subscribe("/".join([MQTT_TOPIC, "events"]))


def mqtt_disconnect(client, userdata, rc):
    """Callback for MQTT disconnects."""
    logging.critical("MQTT disconnected: " + mqtt.connack_string(rc))


def mqtt_message(client, userdata, msg):
    """Callback for MQTT message PUBLISH."""
    try:
        # Decode JSON payload
        data = json.loads(msg.payload.decode())
        logging.debug("Received Device Data from SDR and sent to MQTT: {} : {}".format(msg.topic, json.dumps(data)))
        bridge_event_to_hass(client, msg.topic, data)

    except json.decoder.JSONDecodeError:
        logging.warning("JSON decode error: " + msg.payload.decode())
        return


def sanitize(text):
    """Sanitize a name for Graphite/MQTT use."""
    return (text
            .replace(" ", "_")
            .replace("/", "_")
            .replace(".", "_")
            .replace("&", ""))


def publish_config(mqttc, topic, model, instance, channel, mapping):
    """Publish Home Assistant auto discovery data."""
    global discovery_timeouts

    device_type = mapping["device_type"]
    object_id = "_".join([model.replace("-", "_"), instance])
    object_suffix = mapping["object_suffix"]

    path = "/".join([DISCOVERY_PREFIX, device_type, object_id, object_suffix, "config"])

    # check timeout
    now = time.time()
    if path in discovery_timeouts:
        if discovery_timeouts[path] > now:
            return

    discovery_timeouts[path] = now + DISCOVERY_INTERVAL

    config = mapping["config"].copy()
    config["state_topic"] = "/".join([MQTT_TOPIC, model, instance, channel, topic])
    config["name"] = " ".join([model.replace("-", " "), instance, object_suffix])
    config["unique_id"] = "".join(["rtl433", device_type, instance, object_suffix])
    # config["availability_topic"] = "/".join([MQTT_TOPIC, "status"])
    
    # Do not set an expire_after timeout for the "Last Seen" (time) sensor
    if topic != "time":
        config["expire_after"] = EXPIRE_AFTER

    # add Home Assistant device info
    # Check for missing manufacturer info
    if '-' in model:
        manufacturer, model = model.split("-", 1)
    else:
        manufacturer = 'Unknown'

    device = {}
    device["identifiers"] = instance
    device["name"] = instance
    device["model"] = model
    device["manufacturer"] = manufacturer
    config["device"] = device

    mqttc.publish(path, json.dumps(config),  qos=0, retain=True)
    logging.debug("Device Config was saved to {} : {}".format(path,json.dumps(config)))
            

def bridge_event_to_hass(mqttc, topic, data):
    """Translate some rtl_433 sensor data to Home Assistant auto discovery."""

    if "model" not in data:
        # not a device event
        return
    model = sanitize(data["model"])

    # Safely assign an instance ID
    if "id" in data:
        instance = str(data["id"])
    else:
        # Fallback to the channel, or assign 'no_id' if neither exists
        instance = str(data.get("channel", "no_id"))
        
    if instance == "0" or instance == 0:
        logging.warning("Device Model: {} reported an ID of 0. Skipping..".format(data.get('model', 'Unknown')))
        return
        
    if "channel" in data:
        channel = str(data["channel"])
    else:
        channel = 'A'

    device = '{}-{}'.format(instance, model)
      
    if (whitelist_on == True) and (instance not in whitelist_list):
        # Let's reduce the noise in the log and hide the duplicate notifications.
        if (instance not in blocked):
            logging.info("Device Id:{} Model: {} not in whitelist. Add to the Whitelist to create device in Home Assistant.".format(instance, data.get('model', 'Unknown')))
            blocked.append(instance)
        return

    if (auto_discovery == True):
        # Let's reduce the noise in the log and hide the duplicate notifications.
        if (device not in rate_limited) or ((datetime.now() - rate_limited[device]).total_seconds() > 30):
            logging.debug('Device: {} - Creating/Updating device config in Home Assistant for Auto discovery.'.format(device))
        rate_limited[device] = datetime.now()
        
        # detect known attributes
        for key in data.keys():
            if key in mappings:
                publish_config(mqttc, key, model, instance, channel, mappings[key])
                

def rtl_433_bridge():
    """Run a MQTT Home Assistant auto discovery bridge for rtl_433."""
    logging.basicConfig(format='%(levelname)s:%(message)s', level=LOGLEVEL)
    
    mqttc = mqtt.Client()
    mqttc.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqttc.on_connect = mqtt_connect
    mqttc.on_disconnect = mqtt_disconnect
    mqttc.on_message = mqtt_message

    mqttc.will_set("/".join([MQTT_TOPIC, "status"]), payload="offline", qos=0, retain=True)
    mqttc.connect_async(MQTT_HOST, MQTT_PORT, 60)
    mqttc.loop_start()

    logging.info('Started')

    while True:
        time.sleep(1)


def run():
    """Run main or daemon."""
    # with daemon.DaemonContext(files_preserve=[sock]):
    #  detach_process=True
    #  uid
    #  gid
    #  working_directory
    rtl_433_bridge()


if __name__ == "__main__":

    run()
