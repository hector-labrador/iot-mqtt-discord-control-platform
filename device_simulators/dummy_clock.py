"""
Simulador de "reloj" que publica la hora cada X segundos en <base>/<id>/status
"""

import argparse
import datetime
import time
import paho.mqtt.publish as publish
import config

def parse_args():
    parser = argparse.ArgumentParser(
        description="Simulador de reloj MQTT (publica la hora HH:MM:SS)."
    )
    parser.add_argument("--device-id", default="clock01", help="ID del dispositivo (ej: clock01)")
    parser.add_argument("--time", default=None, help="Hora inicial en formato HH:MM:SS")
    parser.add_argument("--increment", type=int, default=1, help="Incremento en seg. (por defecto: 1)")
    parser.add_argument("--rate", type=int, default=1, help="Mensajes por segundo (1 => 1 msg/seg)")
    return parser.parse_args()

def main():
    args = parse_args()

    # Determinamos la hora de inicio
    if args.time:
        h, m, s = [int(x) for x in args.time.split(":")]
        current_time = datetime.datetime.now().replace(hour=h, minute=m, second=s, microsecond=0)
    else:
        current_time = datetime.datetime.now().replace(microsecond=0)

    # Tópico de publicación
    topic = f"{config.MQTT_BASE_TOPIC}/{args.device_id}/status"

    # Intervalo entre publicaciones basado en la tasa 'rate'
    interval = 1.0 / args.rate
    print(f"[ClockSim] Publicando en '{topic}' cada {interval}s; +{args.increment} seg en cada envío")

    try:
        while True:
            payload = current_time.strftime("%H:%M:%S")
            publish.single(
                topic,
                payload,
                hostname=config.MQTT_BROKER,
                port=config.MQTT_PORT,
                qos=0,
                retain=False
            )
            print(f"[ClockSim] {args.device_id} -> {payload}")
            current_time += datetime.timedelta(seconds=args.increment)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[ClockSim] Detenido por el usuario.")

if __name__ == "__main__":
    main()
