# IoT Device Control Platform (MQTT + Discord)

IoT device management platform built around **MQTT messaging** (Mosquitto broker) and a **Discord bot** interface.  
The system supports device registration, state monitoring, command delivery (ON/OFF), and **rule-based automation**, with simulated devices for testing.

---

## Key Features

- MQTT-based messaging architecture (Mosquitto broker)
- Discord bot commands to manage devices and query state
- Device simulators:
  - Temperature sensor (periodic status publish)
  - ON/OFF switch (command + status topics)
  - Dummy clock (periodic time publish)
- Rule engine for simple automation (conditions → actions)
- Persistence layer (SQLAlchemy) for device registry and rules
- Unit tests included

---

## Technical Concepts Demonstrated

- Publish/Subscribe communication model (MQTT)
- Distributed systems coordination via message broker
- Basic automation / rule-based processing
- Environment-based configuration (`.env`)
- Persistence and data modeling with SQLAlchemy
- Automated testing with `unittest`

---

## Quick Start

### Requirements
- Python 3.10 or 3.11 (avoid 3.12+ due to SQLAlchemy compatibility)
- Mosquitto (MQTT broker)

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
