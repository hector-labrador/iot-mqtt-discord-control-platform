"""
controller.py - recibe mensajes MQTT -> persiste -> notifica
"""

from __future__ import annotations
import datetime as dt
import logging
from typing import Callable, List

from mqtt_client import MQTTClient
import persistence as db

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, base_topic: str):
        self.base_topic = base_topic.rstrip("/")
        self._mqtt = MQTTClient(on_message=self._handle_mqtt_message)
        self._subscribers: List[Callable[[db.Event], None]] = []

    def start(self):
        """Arranca la conexión MQTT y se suscribe a los topics de estado."""
        self._mqtt.connect_and_start()
        # Escucha <base>/<device_id>/status
        self._mqtt.subscribe(f"{self.base_topic}/+/status")

    def register_listener(self, callback: Callable[[db.Event], None]) -> None:
        """Permite que RuleEngine/Bridge se enteren de nuevos eventos."""
        self._subscribers.append(callback)

    def send_command(self, device_id: str, payload: str) -> None:
        """
        Publica <base>/<device_id>/set con el payload especificado.
        Usado para conmutar interruptores (ON/OFF).
        """
        topic = f"{self.base_topic}/{device_id}/set"
        logger.info("Publicando comando %s → %s", topic, payload)
        self._mqtt.publish(topic, payload)

    def request_status(self, device_id: str) -> None:
        """
        Publica un mensaje para “preguntar” el estado actual al dispositivo
        """
        topic = f"{self.base_topic}/{device_id}"
        query_payload = "GET_STATE"  # o algo similar
        logger.info("Pidiendo estado a %s => %s", device_id, query_payload)
        self._mqtt.publish(topic, query_payload)

    def _handle_mqtt_message(self, topic: str, payload: str):
        parts = topic.split("/")
        if len(parts) != 5:
            logger.warning("Topic mal formado (esperaba 5 partes): %s", topic)
            return

        # parts[0] = redes2
        # parts[1] = 9999 (grupo)
        # parts[2] = 99   (pareja)
        # parts[3] = device_id
        # parts[4] = status (subtopic)
        prefix = "/".join(parts[:3])  # "redes2/9999/99"
        device_id = parts[3]
        subtopic = parts[4]

        if subtopic != "status":
            logger.warning("Subtopic inesperado: %s (payload: %s)", subtopic, payload)
            return

        with db.get_session() as session:
            dev = session.query(db.Device).filter_by(device_id=device_id).one_or_none()
            if not dev:
                logger.warning("Mensaje ignorado: Dispositivo '%s' no registrado", device_id)
                return

            dev.last_state = payload
            dev.last_updated = dt.datetime.utcnow()
            session.commit()

            event = db.Event(device_id=device_id, payload=payload)
            session.add(event)
            session.commit()

        # Ahora sí notifica a los listeners
        for cb in self._subscribers:
            cb(event)

