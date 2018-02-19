#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__description__ = "Sinope thermostat MQTT bridge"
__author__ = "Bennett Kanuka"
__credits__ = ["Bennett Kanuka"]
__license__ = "MIT"
__version__ = "0.9"
__maintainer__ = "Bennett Kanuka"
__email__ = "bkanuka@gmail.com"
__status__ = "Development"

import argparse
import logging
import sinopey
import paho.mqtt.client as mqtt
import time
import json
import requests


def main_loop(py_sinope, mqttc, mqtt_server="localhost", mqtt_port=1883):
    try:
        # PySinope setup
        py_sinope.connect()
        logging.debug("Reading gateways")
        py_sinope.read_gateway()

        # MQTT setup
        def on_message(client, obj, msg):
            logging.debug("MQTT message: " + str(msg.payload))
            parsed_msg = json.loads(msg.payload.decode("utf8"))
            logging.debug("Parsed msg: " + str(parsed_msg))
            thermostat = py_sinope.get_thermostat(parsed_msg['name'])
            if "setpoint" in parsed_msg:
                thermostat.setpoint = parsed_msg['setpoint']

        # Assign event callbacks
        mqttc.on_message = on_message

        mqttc.connect(mqtt_server, mqtt_port)
        mqttc.subscribe("sinope/set", 2)

        logging.debug("MQTT Connected")
        mqttc.loop_start()
        logging.debug("MQTT Loop started")

        i = 0
        while True:
            logging.debug("Updating thermostats")
            for gateway in py_sinope.gateways:
                for thermostat in gateway.thermostats:
                    try:
                        thermostat.update()
                    except requests.exceptions.Timeout:
                        logging.warning("Thermostat {}({}) was unreachable".format(thermostat.name, thermostat.id))
                    else:
                        msg = json.dumps({
                            'name': thermostat.name,
                            'temperature': float(thermostat.temperature),
                            'setpoint': float(thermostat.setpoint)
                        })
                        logging.debug("MQTT Publishing: {}".format(msg))
                        mqttc.publish("sinope/status", msg)

            i = i + 1
            if i >= 5:
                logging.info("Refreshing Sinope gateway")
                py_sinope.read_gateway()
                i = 0

            time.sleep(20)

    finally:
        py_sinope.disconnect()
        mqttc.loop_stop()
        logging.debug("MQTT Loop stopped")


def main():
    parser = argparse.ArgumentParser(description=__description__)

    parser.add_argument("--username", "-u",
                        required=True,
                        help="Neviweb username (email address)",
                        )
    parser.add_argument("--password", "-p",
                        required=True,
                        help="Neviweb password",
                        )
    parser.add_argument("--mqtt-server", "-m",
                        required=False,
                        default='localhost',
                        help="MQTT server url or IP",
                        )
    parser.add_argument("--mqtt-port", "-P",
                        required=False,
                        type=int,
                        default=1883,
                        help="MQTT server port",
                        )
    parser.add_argument("--timeout", "-t",
                        required=False,
                        type=int,
                        default=10,
                        help="Neviweb communication timeout",
                        )
    parser.add_argument("--retry", "-r",
                        required=False,
                        type=int,
                        default=5,
                        help="Time to wait before retrying in case of connection error",
                        )
    parser.add_argument("--version",
                        action="version",
                        version="%(prog)s {}".format(__version__)
                        )
    parser.add_argument("--verbose", "-v",
                        dest="verbose_count",
                        action="count",
                        default=0,
                        help="Verbose logging. Can be specified twice."
                        )

    args = parser.parse_args()

    if args.verbose_count == 1:
        logging.basicConfig(level=logging.INFO)
        logging.info("Logging info messages")
    elif args.verbose_count >= 2:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Logging debug messages!")
    else:
        logging.basicConfig(level=logging.WARNING)

    while True:
        try:
            py_sinope = sinopey.Sinope(args.username,
                                       args.password,
                                       args.timeout)
            mqttc = mqtt.Client()
            main_loop(py_sinope,
                      mqttc,
                      mqtt_server=args.mqtt_server,
                      mqtt_port=args.mqtt_port)
        except KeyboardInterrupt:
            break
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            logging.warning('Request Error', exc_info=True)
            time.sleep(args.retry)


if __name__ == "__main__":
    main()
