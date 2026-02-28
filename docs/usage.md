===================================================

    REQUISITOS PREVIOS

• Python 3.10 o 3.11

    Evitar Python 3.12+ por compatibilidad con ciertas versiones de SQLAlchemy.

• Git

• Mosquitto (broker MQTT) instalado y habilitado Ejemplo en Ubuntu: sudo
apt-get update sudo apt-get install -y mosquitto sudo service mosquitto
start

    PREPARAR EL ENTORNO (Python Virtualenv)

cd \~/P3REDES/

    Crea el entorno virtual:
    python3 -m venv .venv

    Actívalo:
    source .venv/bin/activate

    Instala las dependencias:
    pip install -r requirements.txt

NOTA: Si aparece algún error con SQLAlchemy, actualízalo: pip install
--upgrade SQLAlchemy==2.0.38

    CONFIGURACIÓN

    Copia .env.example a .env:
    cp .env.example .env

    Edita .env para establecer los valores (ej.: DISCORD_TOKEN, MQTT_BROKER, etc.)
    Un token Discord falso (p.ej. DISCORD_TOKEN="fake_for_tests") sirve para ejecutar sin errores.

    LEVANTAR MOSQUITTO

• Ubuntu: sudo service mosquitto start

• (O la forma que hayas instalado, Docker, etc.)

    EJECUTAR LA APLICACIÓN PRINCIPAL

Con el entorno virtual activado:

python main.py

Deberás ver logs de conexión a MQTT (host y puerto) y logs del bot de
Discord.

    SIMULADORES DE DISPOSITIVOS

En otra terminal (donde también actives .venv):

• Sensor de temperatura python -m device_simulators.temp_sensor_sim
--device-id temp01 Publica valores aleatorios cada 5 segundos en
redes2/2313/09/temp01/status

• Interruptor ON/OFF python -m device_simulators.switch_sim --device-id
boiler Escucha .../boiler/set, publica ON/OFF en .../boiler/status

• Reloj python -m device_simulators.dummy_clock --device-id clock01
Publica la hora cada X segundos en .../clock01/status

    USO DEL BOT EN DISCORD

Comandos (en el canal donde el bot tenga permisos): !devices (lista
dispositivos registrados) !device add `<id>`{=html} `<type>`{=html} (da
de alta un nuevo dispositivo) !device edit `<id>`{=html}
`<new_type>`{=html} (cambia tipo de dispositivo) !device delete
`<id>`{=html} (elimina dispositivo de la BD) !state `<device_id>`{=html}
(consulta último estado) !switch `<device_id>`{=html} \<on\|off\> (envía
comando ON/OFF) !ask `<device_id>`{=html} (fuerza al sensor a publicar
su estado) !rule list (lista las reglas) !rule add "nombre" "cond"
"action" (crea regla) !rule delete `<id>`{=html} (borra la regla con ese
ID)

    EJECUTAR LOS TESTS UNITARIOS

    Asegúrate de que .env tenga un DISCORD_TOKEN

    Activa el entorno virtual:
    source .venv/bin/activate

    Ejecuta:
    python -m unittest discover tests

Si los tests están configurados correctamente, verás algo como: ......

Ran 6 tests in 0.03s

OK
