# LIRC-docker
This repository arose from my own needs to run LIRC with HomeAssistant, but
I didn't want to install LIRC. I have prepared two containers:
- **Only LIRC installed**: can be used the same as if you had LIRC on your system
- **LIRC + MQTT**: Have a MQTT client alongside LIRC. It subscribes a **topic** and
  run `irsend` using payload data

## Preparation steps
You need to enable the kernel driver for IR in case you're running
the container in a raspberry pi (my case).

Add the following line to your `/boot/firmware/config.txt` or
`/boot/config.txt` (depending of your OS)

```
dtoverlay=gpio-ir,gpio_pin=17 # receiver
dtoverlay=gpio-ir-tx,gpio_pin=18 # transmitter
```

## Common notes
You need to run the container as `--privileged` so it can have access
to required dependencies (e.g. devices). You also need to bind
the configuration file to be used:

```bash
docker run --rm --privileged -v ./path2cfg:/usr/etc/lirc/lircd.conf.d/cfg_name <container> <command>
```

> I have tried [lot of methods](https://stackoverflow.com/questions/30059784/docker-access-to-raspberry-pi-gpio-pins)
> to avoid the usage of `--privileged` without much success
> (I'm not too versed about linux internals). Let me know if you find a way
> to give the minimal permissions to the container 🙂

## LIRC
```bash
docker run --rm --privileged \
    -v ./path2cfg:/usr/etc/lirc/lircd.conf.d/cfg_name \
    scmanjarrez/lirc <command>
```

```bash
docker run --rm --privileged \
    -v ./leds.lircd.conf:/usr/etc/lirc/lircd.conf.d/leds.lircd.conf \
    scmanjarrez/lirc irsend SEND_ONCE leds KEY_ON
```

## LIRC & MQTT
You need to define a set of environment variables so MQTT client can
connect to broker and subscribe to the topic:

```bash
docker run --rm --privileged \
    -v ./path2cfg:/usr/etc/lirc/lircd.conf.d/cfg_name \
    -e MQTT_HOST=<broker_hostname/ip> \
    -e MQTT_PORT=<broker_port/ip> \
    -e MQTT_USER=<user> \
    -e MQTT_PASS=<passwd> \
    -e MQTT_TOPIC=<topic> \
    scmanjarrez/lirc:mqtt
```

```bash
docker run --rm --privileged \
    -v ./leds.lircd.conf:/usr/etc/lirc/lircd.conf.d/leds.lircd.conf \
    -e MQTT_HOST=mqtt \
    -e MQTT_PORT=1884 \
    -e MQTT_USER=hass \
    -e MQTT_PASS=strong_password \
    -e MQTT_TOPIC=lirc \
    scmanjarrez/lirc:mqtt
```

> **Note**: You can skip any environment, the default value will be used instead:
> ```
> MQTT_HOST: localhost
> MQTT_PORT: 1883
> MQTT_USER: None # No authentication required ("allow_anonymous true" if using eclipse-mosquitto)
> MQTT_PASS: None
> MQTT_TOPIC: lirc
> ```

The payload must be a json with the following format:
```json
{
  "rc": "remote-name",
  "key": "key-name, without KEY_"
}
```

```json
{
  "rc": "leds",
  "key": "ON"
}
```

### docker compose
This is a small example for running with HomeAssistant, I'm using the default
topic of the container to send messages: **lirc**
```json
{"rc": "leds", "key": "ON"}
```

```yaml
version: '3'
services:
  hass:
    image: ghcr.io/home-assistant/home-assistant:stable
    network_mode: "host"
    privileged: true
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
      - ./hass-config:/config
    depends_on:
      - mqtt
    restart: unless-stopped

  mqtt:
    image: eclipse-mosquitto:latest
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./mqtt-config:/mosquitto/config # already configured with allow_anonymous false
      - ./mqtt-data:/mosquitto/data
      - ./mqtt-log:/mosquitto/log
    ports:
      - 1883:1883
      - 9001:9001
    restart: unless-stopped

  lirc:
    image: scmanjarrez/lirc:mqtt
    privileged: true
    environment:
      - MQTT_HOST=mqtt
      - MQTT_USER=hass
      - MQTT_PASS=strong_password
    volumes:
      - ./leds.lircd.conf:/usr/etc/lirc/lircd.conf.d/leds.lircd.conf
    depends_on:
      - mqtt
    restart: unless-stopped
```
