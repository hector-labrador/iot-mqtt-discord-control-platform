"""
Pruebas unitarias de los simuladores (switch, sensor, clock).
"""

import unittest
import argparse
from unittest.mock import patch, MagicMock


from device_simulators.temp_sensor_sim import parse_args as parse_args_sensor
from device_simulators.switch_sim import SwitchSim
from device_simulators.dummy_clock import parse_args as parse_args_clock

class TestDeviceSimulators(unittest.TestCase):
    def test_sensor_parse_args(self):
        """
        Verifica que el sensor parsee bien los parámetros de línea de comandos.
        """
        argv = [
            "--device-id", "temp02",
            "--min", "18.5",
            "--max", "22.5",
            "--period", "3.0"
        ]
        with patch('sys.argv', ["test_sensor.py"] + argv):
            args = parse_args_sensor()
            self.assertEqual(args.device_id, "temp02")
            self.assertAlmostEqual(args.min, 18.5)
            self.assertAlmostEqual(args.max, 22.5)
            self.assertAlmostEqual(args.period, 3.0)

    def test_clock_parse_args(self):
        """
        Verifica que el clock parsee bien sus parámetros.
        """
        argv = [
            "--device-id", "clockTest",
            "--time", "09:30:00",
            "--increment", "60",
            "--rate", "2"
        ]
        with patch('sys.argv', ["test_clock.py"] + argv):
            args = parse_args_clock()
            self.assertEqual(args.device_id, "clockTest")
            self.assertEqual(args.time, "09:30:00")
            self.assertEqual(args.increment, 60)
            self.assertEqual(args.rate, 2)

    @patch("paho.mqtt.client.Client")
    def test_switch_changes_state_on_off(self, mock_mqtt_client_class):
        """
        Comprueba que el switch cambie de OFF -> ON y publique su estado.
        Empleamos mock de paho-mqtt para no depender de un broker real.
        """
        # Creamos una instancia de SwitchSim con device_id="boilerTest"
        sim = SwitchSim(device_id="boilerTest")


        sim.cli.loop_start = MagicMock()
        sim.cli.loop_stop = MagicMock()

        # Forzamos una recepción de mensaje "ON" en el topic /set
        fake_msg = MagicMock()
        fake_msg.payload.decode.return_value = "ON"
        sim._on_message(None, None, fake_msg)
        self.assertEqual(sim.state, "ON")

        # Forzamos una recepción de mensaje "OFF"
        fake_msg.payload.decode.return_value = "OFF"
        sim._on_message(None, None, fake_msg)
        self.assertEqual(sim.state, "OFF")

        # Verificamos que se haya hecho publish() en cada cambio
        #    (mock_mqtt_client_class.return_value es el "self.cli")
        cli_instance = mock_mqtt_client_class.return_value
        self.assertTrue(cli_instance.publish.called)

if __name__ == "__main__":
    unittest.main()
