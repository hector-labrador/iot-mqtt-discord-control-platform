"""
mqtt_client.py - Pequeño wrapper sobre paho-mqtt para simplificar callbacks
"""

from __future__ import annotations
import logging
import queue
from typing import Callable, Optional

import paho.mqtt.client as mqtt
import config

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(
        self,
        on_message: Callable[[str, str], None],
        on_connect: Optional[Callable[[mqtt.Client], None]] = None,
    ) -> None:
        self._on_external_message = on_message
        self._on_external_connect = on_connect

        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def connect_and_start(self) -> None:
        """Conecta al broker y arranca el loop de MQTT en un hilo aparte."""
        self._client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
        self._client.loop_start()

    def subscribe(self, topic: str) -> None:
        logger.debug("Suscribiéndose a %s", topic)
        self._client.subscribe(topic)

    def publish(self, topic: str, payload: str, retain: bool = False) -> None:
        """Publica un mensaje en el topic indicado."""
        self._client.publish(topic, payload, retain=retain)

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc) -> None:
        """Callback interno de paho-mqtt al conectar."""
        if rc == 0:
            logger.info("Conectado a MQTT broker %s:%s", config.MQTT_BROKER, config.MQTT_PORT)
            if self._on_external_connect:
                self._on_external_connect(client)
        else:
            logger.error("No se pudo conectar al broker, rc=%s", rc)

    def _on_message(self, client, userdata, msg) -> None:
        """Callback interno de paho-mqtt al recibir un mensaje."""
        topic = msg.topic
        payload = msg.payload.decode(errors="ignore")
        logger.debug("Mensaje MQTT %s => %s", topic, payload)
        self._on_external_message(topic, payload)
