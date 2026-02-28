"""
bridge.py - Puente entre Controller y bot de Discord
"""

from __future__ import annotations
import asyncio
import logging
import discord
import persistence as db
import config

logger = logging.getLogger(__name__)

class Bridge:
    def __init__(self, controller, bot):
        self.controller = controller
        self.bot: discord.Client | discord.ext.commands.Bot = bot
        self.event_q: asyncio.Queue[db.Event] = asyncio.Queue()

        # Controller -> cola interna
        controller.register_listener(lambda ev: self.event_q.put_nowait(ev))
        # Tarea asíncrona que publicará en Discord
        bot.loop.create_task(self._publisher_task())

    # - Métodos usados por el bot -
    def list_devices(self):
        with db.get_session() as s:
            return s.query(db.Device).all()

    def get_device(self, device_id: str):
        with db.get_session() as s:
            return s.query(db.Device).filter_by(device_id=device_id).one_or_none()

    def add_device(self, device_id: str, device_type: str):
        with db.get_session() as s:
            existing = s.query(db.Device).filter_by(device_id=device_id).one_or_none()
            if existing:
                return False, "Ya existe un dispositivo con ese ID"
            new_dev = db.Device(device_id=device_id, device_type=device_type)
            s.add(new_dev)
            s.commit()
        return True, "Dispositivo creado correctamente"

    def edit_device_type(self, device_id: str, new_type: str):
        with db.get_session() as s:
            dev = s.query(db.Device).filter_by(device_id=device_id).one_or_none()
            if not dev:
                return False, "Dispositivo no encontrado"
            dev.device_type = new_type
            s.commit()
        return True, "Tipo de dispositivo actualizado"

    def delete_device(self, device_id: str):
        with db.get_session() as s:
            dev = s.query(db.Device).filter_by(device_id=device_id).one_or_none()
            if not dev:
                return False, "Dispositivo no encontrado"
            s.delete(dev)
            s.commit()
        return True, "Dispositivo borrado correctamente"

    def get_state(self, device_id: str):
        with db.get_session() as s:
            dev = s.query(db.Device).filter_by(device_id=device_id).one_or_none()
            return dev.last_state if dev else None

    def switch_device(self, device_id: str, payload: str):
        self.controller.send_command(device_id, payload)

    def ask_device_status(self, device_id: str):
        """Publica un mensaje de 'GET_STATE' hacia el dispositivo para que responda."""
        self.controller.request_status(device_id)

    #Publicamos eventos en discord
    async def _publisher_task(self):
        await self.bot.wait_until_ready()
        channel = self._find_default_channel()
        if not channel:
            logger.warning("Bridge: no se encontró canal con permisos de envío")
            return

        logger.info("Bridge publicará eventos en #%s", channel.name)
        while True:
            ev = await self.event_q.get()
            await channel.send(f"📟 **{ev.device_id}** → `{ev.payload}`")

    def _find_default_channel(self):
        for guild in self.bot.guilds:
            if config.DISCORD_GUILD and guild.name != config.DISCORD_GUILD:
                continue
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    return ch
        return None
