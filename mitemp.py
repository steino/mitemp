#!/usr/bin/env python3

from mitemp_bt.mitemp_bt_poller import MiTempBtPoller
from btlewrap.bluepy import BluepyBackend
from btlewrap.base import BluetoothBackendException
import paho.mqtt.client as mqtt
import time
import json
import logging

_LOGGER = logging.getLogger(__name__)


poller = MiTempBtPoller('4c:65:a8:db:91:ef', cache_timeout=300, backend=BluepyBackend)

poller.ble_timeout = 10
poller.retries = 2

client = mqtt.Client()
client.connect("192.168.1.138", 1883, 60)

tr = json.dumps({
    'device_class': 'temperature',
    'name': 'Xiaomi Stue Temperature',
    'state_topic': 'homeassistant/sensor/xiaomi/stue/state',
    'unit_of_measurement': '°C',
    'value_template': '{{ value_json.temperature }}'
    })

hr = json.dumps({
    'device_class': 'humidity',
    'name': 'Xiaomi Stue Humidity',
    'state_topic': 'homeassistant/sensor/xiaomi/stue/state',
    'unit_of_measurement': '%',
    'value_template': '{{ value_json.humidity }}'
    })

br = json.dumps({
    'device_class': 'battery',
    'name': 'Xiaomi Stue Battery',
    'state_topic': 'homeassistant/sensor/xiaomi/stue/state',
    'unit_of_measurement': '%',
    'value_template': '{{ value_json.battery }}'
    })

client.publish("homeassistant/sensor/xiaomi/stue_temperature/config", tr, retain=True)
client.publish("homeassistant/sensor/xiaomi/stue_humidity/config", hr, retain=True)
client.publish("homeassistant/sensor/xiaomi/stue_battery/config", br, retain=True)

client.loop_start()

while True:
    try:
        r = json.dumps({
            'temperature': poller.parameter_value("temperature"),
            'humidity': poller.parameter_value("humidity"),
            'battery': poller.parameter_value("battery")
            })
    except IOError as ioerr:
        _LOGGER.warning("Polling error %s", ioerr)
    except BluetoothBackendException as bterror:
        _LOGGER.warning("Polling error %s", bterror)
    finally:
        client.publish("homeassistant/sensor/xiaomi/stue/state", r)
                print(r)

        time.sleep(300)
