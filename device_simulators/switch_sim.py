"""
Simulador de un interruptor ON/OFF.
"""

import argparse
import logging
import time
import paho.mqtt.client as mqtt
import config

logging.basicConfig(level=logging.INFO)

class SwitchSim:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.topic_set = f"{config.MQTT_BASE_TOPIC}/{device_id}/set"
        self.topic_status = f"{config.MQTT_BASE_TOPIC}/{device_id}/status"
        self.state = "OFF"
        self.cli = mqtt.Client()
        self.cli.on_message = self._on_message

    def start(self):
        """Arranca la conexión al broker y publica el estado inicial."""
        self.cli.connect(config.MQTT_BROKER, config.MQTT_PORT)
        self.cli.subscribe(self.topic_set)
        self.cli.loop_start()

        # Publicamos el estado inicial
        self.cli.publish(self.topic_status, self.state, retain=True)
        logging.info("SwitchSim '%s' listo. Estado inicial: %s", self.device_id, self.state)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cli.loop_stop()

    def _on_message(self, client, userdata, msg):
        """
        Cuando recibe ON/OFF en /set, cambia el estado y lo publica en /status.
        """
        payload = msg.payload.decode().upper()
        if payload in {"ON", "OFF"}:
            self.state = payload
            self.cli.publish(self.topic_status, self.state, retain=True)
            logging.info("[SwitchSim] %s => %s", self.device_id, self.state)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-id", default="boiler")
    args = parser.parse_args()
    SwitchSim(args.device_id).start()

if __name__ == "__main__":
    main()
