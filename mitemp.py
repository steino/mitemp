#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mitemp_bt.mitemp_bt_poller import MiTempBtPoller
from btlewrap.bluepy import BluepyBackend
from btlewrap.base import BluetoothBackendException
import paho.mqtt.client as mqtt
import time
import json
import logging
import yaml

_LOGGER = logging.getLogger(__name__)

with open("config.yaml", 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit(1)

client = mqtt.Client()
client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)

for device in config["devices"]:
    device_id = list(device.keys())[0]
    address = device[device_id]["address"]
    name = device[device_id]["name"]

    if config["mqtt"]["discovery"]:
        tr = json.dumps({
            'device_class': 'temperature',
            'name': '%s Temperature' % name,
            'state_topic': '%s/sensor/xiaomi/%s/state' % (config["mqtt"]["state_topic"], device_id),
            'unit_of_measurement': '°C',
            'value_template': '{{ value_json.temperature }}'
            })

        hr = json.dumps({
            'device_class': 'humidity',
            'name': '%s Humidity' % name,
            'state_topic': '%s/sensor/xiaomi/%s/state' % (config["mqtt"]["state_topic"], device_id),
            'unit_of_measurement': '%',
            'value_template': '{{ value_json.humidity }}'
            })

        br = json.dumps({
            'device_class': 'battery',
            'name': '%s Battery' % name,
            'state_topic': '%s/sensor/xiaomi/%s/state' % (config["mqtt"]["state_topic"], device_id),
            'unit_of_measurement': '%',
            'value_template': '{{ value_json.battery }}'
            })

        client.publish("%s/sensor/xiaomi/%s_temperature/config" % (config["mqtt"]["state_topic"], device_id), tr, retain=True)
        client.publish("%s/sensor/xiaomi/%s_humidity/config" % (config["mqtt"]["state_topic"], device_id), hr, retain=True)
        client.publish("%s/sensor/xiaomi/%s_battery/config" % (config["mqtt"]["state_topic"], device_id), br, retain=True)

        device[device_id]["poller"] = MiTempBtPoller(address, cache_timeout=300, backend=BluepyBackend)


client.loop_start()

while True:
    for device in config["devices"]:
        device_id = list(device.keys())[0]
        poller = device[device_id]["poller"]
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
            client.publish("%s/sensor/xiaomi/%s/state" % (config["mqtt"]["state_topic"], device_id), r)
            print(r)

    time.sleep(300)
