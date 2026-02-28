"""
Punto de entrada del proyecto.
Arranca Controller, RuleEngine, Bot y Bridge.
"""

import asyncio
import logging
import sys

import config
from controller import Controller
from rule_engine import RuleEngine
from bot import HomeBot
from bridge import Bridge
import persistence as db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    # 1) Inicializa la BD (si no existe)
    db.init_db()

    # 2) Crea Controller y Rule Engine
    controller = Controller(config.MQTT_BASE_TOPIC)
    controller.start()
    rule_engine = RuleEngine(controller)

    # 3) Crea el Bot, pasándole un "bridge_factory" y el rule_engine
    def bridge_factory(bot):
        return Bridge(controller, bot)

    bot = HomeBot(bridge_factory, rule_engine)

    # 4) Lanza la aplicación asíncrona
    async def _runner():
        await bot.start(config.DISCORD_TOKEN)

    try:
        asyncio.run(_runner())
    except KeyboardInterrupt:
        logger.warning("Interrumpido – cerrando.")
        sys.exit(0)

if __name__ == "__main__":
    main()
