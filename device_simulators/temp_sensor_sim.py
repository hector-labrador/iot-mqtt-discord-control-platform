"""
Simulador de un sensor de temperatura.
Publica un valor aleatorio cada N segundos en su /status.
"""

from __future__ import annotations
import argparse
import asyncio
import random
import paho.mqtt.publish as publish
import config

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulador de sensor de temperatura MQTT")
    parser.add_argument("--device-id", default="temp01", help="ID del dispositivo sensor")
    parser.add_argument("--min", type=float, default=19.0, help="Temperatura mínima")
    parser.add_argument("--max", type=float, default=23.0, help="Temperatura máxima")
    parser.add_argument("--period", type=float, default=5.0, help="Periodo de envío (s)")
    return parser.parse_args()

async def main() -> None:
    args = parse_args()
    topic = f"{config.MQTT_BASE_TOPIC}/{args.device_id}/status"
    print(f"[TempSensor] Publicando en '{topic}' cada {args.period}s")

    while True:
        value = random.uniform(args.min, args.max)
        payload = f"{value:.1f}"
        publish.single(
            topic,
            payload,
            hostname=config.MQTT_BROKER,
            port=config.MQTT_PORT,
            qos=0,
            retain=False,
        )
        print(f"[TempSensor] {args.device_id} -> {payload}")
        await asyncio.sleep(args.period)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[TempSensor] Detenido por el usuario.")
