"""
Pruebas del Controller: rechazo de dispositivos desconocidos, notificación a listeners, etc.
"""

import unittest
from unittest.mock import patch, MagicMock
import persistence as db
from controller import Controller
from mqtt_client import MQTTClient
from rule_engine import RuleEngine

class TestController(unittest.TestCase):
    def setUp(self):
        """
        Se ejecuta antes de cada test. Prepara una BD en memoria (o mock),
        y crea un Controller con un MQTTClient mockeado.
        """
        db._engine.dispose()
        db._engine = db.create_engine("sqlite:///:memory:", echo=False)
        db.Base.metadata.create_all(bind=db._engine)
        db.SessionLocal.configure(bind=db._engine)

        self.mock_mqtt = MagicMock(spec=MQTTClient)
        with patch("controller.MQTTClient", return_value=self.mock_mqtt):
            self.controller = Controller("redes2/9999/99")

        # Arrancamos el Controller
        self.controller.start()

    def test_ignore_unregistered_device(self):
        """
        Verifica que el Controller ignora (rechaza) mensajes de un device_id no registrado.
        """
        # Simulamos llegada de mensaje: topic => "redes2/9999/99/no_existe/status"
        # y payload => "SOME_STATE"
        self.controller._handle_mqtt_message(
            "redes2/9999/99/no_existe/status",
            "SOME_STATE"
        )
        # Comprobamos en la BD que no haya creado un device "no_existe"
        with db.get_session() as session:
            dev = session.query(db.Device).filter_by(device_id="no_existe").one_or_none()
            self.assertIsNone(dev, "No debería crear el device, sino ignorarlo.")

    def test_notify_listeners(self):
        """
        Verifica que tras recibir un mensaje válido, se notifica a los 'listeners' (RuleEngine, Bridge, etc).
        """
        # Creamos un device en la BD para que esté registrado
        with db.get_session() as session:
            d = db.Device(device_id="sensorTest", device_type="sensor")
            session.add(d)
            session.commit()
            d_id = d.id

        # Registramos un listener de prueba
        fake_listener = MagicMock()
        self.controller.register_listener(fake_listener)

        # Llega un mensaje con device_id="sensorTest"
        self.controller._handle_mqtt_message(
            "redes2/9999/99/sensorTest/status",
            "22.5"
        )

        # Revisamos que 'fake_listener' se invocó una vez con un evento
        fake_listener.assert_called_once()
        called_args = fake_listener.call_args[0]
        event_obj = called_args[0]
        self.assertEqual(event_obj.device_id, "sensorTest")
        self.assertEqual(event_obj.payload, "22.5")

        # Revisamos que la BD se haya actualizado con last_state=22.5
        with db.get_session() as session:
            d2 = session.query(db.Device).get(d_id)
            self.assertEqual(d2.last_state, "22.5")

    def test_controller_with_rule_engine(self):
        """
        Comprueba que se integra con RuleEngine sin fallar.
        """
        # Crea RuleEngine
        re = RuleEngine(self.controller)
        # No hay reglas, pero al registrar uno con (controller.register_listener)
        # ya tenemos su "listener" en la pipeline.
        # Simulamos un dispositivo conocido:
        with db.get_session() as s:
            s.add(db.Device(device_id="some_dev", device_type="switch"))
            s.commit()

        # Mandamos un mensaje:
        self.controller._handle_mqtt_message(
            "redes2/9999/99/some_dev/status",
            "ON"
        )
  
        with db.get_session() as s:
            evt = s.query(db.Event).filter_by(device_id="some_dev").first()
            self.assertIsNotNone(evt, "Se debió persistir un evento")

if __name__ == "__main__":
    unittest.main()
