import logging
import persistence as db

logger = logging.getLogger(__name__)

class RuleEngine:
    """Carga reglas desde la BD y evalúa cada evento que llega."""

    def __init__(self, controller):
        self.controller = controller
        self._rules = []
        self._load_rules_from_db()

        # el controller avisará de cada nuevo Event
        controller.register_listener(self._on_event)

    def _load_rules_from_db(self) -> None:
        """Lee todas las reglas de la tabla 'rules'."""
        with db.get_session() as s:
            self._rules = s.query(db.Rule).all()
        logger.info("Cargadas %d reglas", len(self._rules))

    def reload_rules(self) -> None:
        """
        Permite recargar las reglas desde la BD sin reiniciar el motor.
        """
        self._load_rules_from_db()
        logger.info("Las reglas se han recargado correctamente.")

    def _on_event(self, event: db.Event) -> None:
        """
        Para cada evento, comprueba las reglas y ejecuta la acción si procede.
        """
        for rule in self._rules:
            try:
                # Evaluamos la condición textual:
                if eval(rule.condition, {}, {"event": event}):
                    logger.info("Regla '%s' disparada", rule.name)
                    exec(rule.action, {}, {"controller": self.controller, "event": event})
            except Exception as exc:
                logger.error("Error en regla '%s': %s", rule.name, exc)
