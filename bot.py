"""
bot.py - Bot de Discord para gestionar dispositivos y reglas
"""

import logging
import discord
from discord.ext import commands
import persistence as db

logger = logging.getLogger(__name__)

class HomeBot(commands.Bot):
    def __init__(self, bridge_factory, rule_engine):
        """
        bridge_factory: factoría que crea el 'Bridge'
        rule_engine: referencia al motor de reglas (para recargar al crear/borrar reglas)
        """
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        self.bridge_factory = bridge_factory
        self.bridge = None
        self.rule_engine = rule_engine

    async def setup_hook(self):
        # Se crea el Bridge cuando el bot ya está inicializado
        self.bridge = self.bridge_factory(self)

        @self.command(name="devices")
        async def _devices(ctx):
            """Muestra la lista de dispositivos registrados en la BD."""
            devices = self.bridge.list_devices()
            if not devices:
                await ctx.send("(Sin dispositivos registrados)")
                return
            lines = [
                f"• **{d.device_id}** ({d.device_type}) — último estado: `{d.last_state}`"
                for d in devices
            ]
            await ctx.send("\n".join(lines))

        @self.command(name="state")
        async def _state(ctx, device_id: str):
            """
            Muestra el último estado conocido de un dispositivo (sin forzar que lo publique).
            """
            state = self.bridge.get_state(device_id)
            if state is None:
                await ctx.send(f"Dispositivo '{device_id}' desconocido o sin estado")
            else:
                await ctx.send(f"{device_id} ⇒ estado '{state}'")

        @self.command(name="switch")
        async def _switch(ctx, device_id: str, onoff: str):
            """
            Envía un comando ON/OFF a un dispositivo interruptor.
            Ejemplo: !switch boiler on
            """
            if onoff.lower() not in {"on", "off"}:
                await ctx.send("Uso: !switch <device_id> <on|off>")
                return
            payload = onoff.upper()
            self.bridge.switch_device(device_id, payload)
            await ctx.send(f"Enviado {payload} a {device_id}")

        # Comando para “forzar” a un sensor que publique su estado
        @self.command(name="ask")
        async def _ask(ctx, device_id: str):
            """
            Pregunta al dispositivo su estado, publicando un payload GET_STATE en <base>/<device_id>
            El dispositivo responderá a su /status.
            """
            dev = self.bridge.get_device(device_id)
            if not dev:
                await ctx.send(f"No se encontró el dispositivo '{device_id}' en la BD.")
                return
            # Enviamos "GET_STATE" para que el sensor responda
            self.bridge.ask_device_status(device_id)
            await ctx.send(f"Estado solicitado a '{device_id}'. Espera su respuesta...")

        # Comando para gestionar dispositivos
        @self.command(name="device")
        async def _device(ctx, subcmd: str = "", *args):
            """
            Gestiona dispositivos: list, add, edit, delete
            Ejemplos:
              !device list
              !device add <device_id> <device_type>
              !device edit <device_id> <new_type>
              !device delete <device_id>
            """
            subcmd = subcmd.lower()

            if subcmd == "list":
                devs = self.bridge.list_devices()
                if not devs:
                    await ctx.send("No hay dispositivos registrados.")
                    return
                lines = [f"**{d.device_id}** ({d.device_type}) - last: {d.last_state}" for d in devs]
                await ctx.send("\n".join(lines))

            elif subcmd == "add":
                # !device add <device_id> <device_type>
                if len(args) < 2:
                    await ctx.send("Uso: !device add <device_id> <device_type>")
                    return
                device_id, device_type = args
                ok, msg = self.bridge.add_device(device_id, device_type)
                await ctx.send(msg)

            elif subcmd == "edit":
                # !device edit <device_id> <new_type>
                if len(args) < 2:
                    await ctx.send("Uso: !device edit <device_id> <new_type>")
                    return
                device_id, new_type = args
                ok, msg = self.bridge.edit_device_type(device_id, new_type)
                await ctx.send(msg)

            elif subcmd == "delete":
                # !device delete <device_id>
                if not args:
                    await ctx.send("Uso: !device delete <device_id>")
                    return
                device_id = args[0]
                ok, msg = self.bridge.delete_device(device_id)
                await ctx.send(msg)

            else:
                usage = (
                    "Uso: !device <subcmd> [args]\n"
                    "  subcmd: list | add | edit | delete\n"
                    "Ejemplo:\n"
                    "  !device list\n"
                    "  !device add sensor01 sensor\n"
                    "  !device edit sensor01 switch\n"
                    "  !device delete sensor01\n"
                )
                await ctx.send(usage)

        # Comando para gestionar reglas
        @self.command(name="rule")
        async def _rule(ctx, subcommand: str = "", *args):
            """
            Gestiona reglas: list, add, delete
            Ejemplos:
              !rule list
              !rule add "ReglaTemperatura" "float(event.payload)>25" "controller.send_command('boiler','ON')"
              !rule delete 3
            """
            subcommand = subcommand.lower()

            if subcommand == "list":
                with db.get_session() as session:
                    all_rules = session.query(db.Rule).all()
                    if not all_rules:
                        await ctx.send("No hay reglas registradas.")
                        return
                    lines = []
                    for r in all_rules:
                        lines.append(
                            f"**ID {r.id}**: {r.name}\n"
                            f"  - condition: `{r.condition}`\n"
                            f"  - action: `{r.action}`"
                        )
                    await ctx.send("\n\n".join(lines))

            elif subcommand == "add":
                """
                Esperamos 3 argumentos:
                  1) Nombre de la regla
                  2) condition (expresión Python, p.ej. float(event.payload)>25)
                  3) action (código Python, p.ej. controller.send_command('boiler','ON'))
                """
                try:
                    rule_name, rule_condition, rule_action = args
                except ValueError:
                    usage_text = (
                        "Uso: !rule add \"<nombre>\" \"<cond>\" \"<action>\"\n"
                        "Ej: !rule add \"ReglaTempAlta\" \"float(event.payload)>25\" "
                        "\"controller.send_command('boiler','ON')\""
                    )
                    await ctx.send(usage_text)
                    return

                with db.get_session() as session:
                    new_rule = db.Rule(
                        name=rule_name,
                        condition=rule_condition,
                        action=rule_action,
                    )
                    session.add(new_rule)
                    session.commit()

                self.rule_engine.reload_rules()
                await ctx.send(f"Regla '{rule_name}' añadida con éxito.")

            elif subcommand == "delete":
                # Elimina la regla según su ID en la tabla 'rules'
                if not args:
                    await ctx.send("Uso: !rule delete <rule_id>")
                    return

                rule_id = args[0]
                with db.get_session() as session:
                    rule_obj = session.query(db.Rule).get(rule_id)
                    if not rule_obj:
                        await ctx.send(f"No se encontró la regla con ID {rule_id}")
                        return
                    session.delete(rule_obj)
                    session.commit()

                self.rule_engine.reload_rules()
                await ctx.send(f"Regla con ID {rule_id} eliminada.")
            else:
                await ctx.send(
                    "Subcomandos disponibles: list, add, delete\n"
                    "Ej: !rule list\n"
                    "    !rule add \"nombre\" \"cond\" \"action\"\n"
                    "    !rule delete <id>"
                )
