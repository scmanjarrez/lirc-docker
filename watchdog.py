# SPDX-License-Identifier: MIT

# Copyright (c) 2024 scmanjarrez. All rights reserved.
# This work is licensed under the terms of the MIT license.


import asyncio
import json
import logging
import os
import signal
import sys

import gmqtt
import lirc

LOG = logging.getLogger("lirc-watchdog")
STOP = asyncio.Event()


class Listener:
    def __init__(self, host, port, user, passwd, topic, log=None):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.topic = topic
        self.mqtt = gmqtt.Client("lirc-watchdog")
        if self.user is not None:
            LOG.debug("Authenticated login")
            self.mqtt.set_auth_credentials(self.user, self.passwd)
        else:
            LOG.debug("Anonymous login")
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.on_message = self.on_message
        self.lirc = lirc.Client()

    async def connect(self):
        await self.mqtt.connect(self.host)

    async def subscribe(self):
        self.mqtt.subscribe(self.topic)

    async def disconnect(self):
        await self.mqtt.disconnect()

    def on_connect(self, client, flags, rc, properties):
        LOG.debug("CONNECTED")

    def on_disconnect(self, client, packet, exc=None):
        LOG.debug("DISCONNECTED")

    def on_message(self, client, topic, payload, qos, properties):
        LOG.info(f"MSG RECEIVED ({topic}): {payload}")
        pay = json.loads(payload)
        self.lirc.send_once(pay["rc"], f"KEY_{pay['key']}")

    def on_subscribe(self, client, mid, qos, properties):
        LOG.debug("SUBSCRIBED")


def ask_exit(*args):
    LOG.info("Exiting...")
    STOP.set()


def setup_logger(log_level):
    LOG.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    LOG.addHandler(handler)


async def main(*args):
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)
    cl = Listener(*args)
    await cl.connect()
    await cl.subscribe()
    await STOP.wait()


if __name__ == "__main__":
    setup_logger(os.environ.get("LOG_LEVEL", "INFO"))
    asyncio.run(
        main(
            os.environ.get("MQTT_HOST", "localhost"),
            os.environ.get("MQTT_PORT", 1883),
            os.environ.get("MQTT_USER", None),
            os.environ.get("MQTT_PASS", None),
            os.environ.get("MQTT_TOPIC", "lirc"),
        )
    )
