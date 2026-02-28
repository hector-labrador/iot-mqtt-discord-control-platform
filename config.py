# --- config.py ---
"""Global configuration, mostly from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()

# MQTT
MQTT_BROKER: str = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT: int = int(os.getenv("MQTT_PORT", 1883))
MQTT_BASE_TOPIC: str = os.getenv("MQTT_BASE_TOPIC", "redes2/2303/01")

# SQLite database file
SQLITE_DB: str = os.getenv("SQLITE_DB", "home_auto.db")

# Discord bot
DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD: str | None = os.getenv("DISCORD_GUILD")

assert DISCORD_TOKEN, (
    "DISCORD_TOKEN is not set! Add it to .env or env‑vars before running."
)

# Misc
DEBUG: bool = os.getenv("DEBUG", "0") == "1"