"""Sensor mixin for Pool Control integration."""

import logging
from typing import Optional

from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class SensorMixin:
    """Mixin class providing sensor methods for Pool Control integration."""

    def _readTemperature(self, entity_id: str, label: str) -> Optional[float]:
        """Lit une sonde de température, ou None s'il n'y a pas de mesure.

        Une entité absente ou un état non numérique ("unavailable",
        "unknown") sont des situations courantes et passagères : elles ne
        valent pas 0 °C, elles ne valent rien. Les appelants doivent
        conserver leur état précédent plutôt que de décider sur une valeur
        fantôme — une sonde d'air muette désarmait la sécurité gel.

        Le cron relit la sonde toutes les minutes : seules les transitions
        sont journalisées, pas chaque lecture.
        """

        state = self.hass.states.get(entity_id)
        value = None
        reason = ""

        if state is None:
            reason = "entité introuvable"
        else:
            try:
                value = float(state.state)
            except (TypeError, ValueError):
                reason = f"état non numérique ({state.state})"

        # Attribut créé à la volée : les mixins ne chaînent pas leurs __init__
        outages = getattr(self, "_temperatureOutages", None)
        if outages is None:
            outages = self._temperatureOutages = {}

        if value is None:
            if not outages.get(entity_id):
                outages[entity_id] = True
                _LOGGER.warning(
                    "%s : pas de mesure sur %s (%s), dernière décision conservée",
                    label,
                    entity_id,
                    reason,
                )
            return None

        if outages.get(entity_id):
            outages[entity_id] = False
            _LOGGER.info("%s : mesure de nouveau disponible sur %s", label, entity_id)

        return value

    def getTemperatureWater(self) -> Optional[float]:
        """Récupére la température de l'eau, ou None faute de mesure."""

        return self._readTemperature(self.temperatureWater, "Température de l'eau")

    def getTemperatureOutdoor(self) -> Optional[float]:
        """Récupére la température de l'air, ou None faute de mesure."""

        return self._readTemperature(self.temperatureOutdoor, "Température de l'air")

    def getTemperatureWaterOrLast(self) -> Optional[float]:
        """Mesure courante de l'eau, ou la dernière validée si la sonde est muette.

        Lecture seule : le secours est écrit par ``recordTemperatureWater``,
        depuis les seuls points où les gardes d'échantillonnage sont passées.
        None n'est renvoyé que si aucune mesure n'a jamais été validée, auquel
        cas le calcul de la plage est reporté.
        """

        temperatureWater = self.getTemperatureWater()

        if temperatureWater is not None:
            return temperatureWater

        derniere = self.get_data("temperatureWaterDerniere")
        return float(derniere) if derniere is not None else None

    def recordTemperatureWater(self, temperatureWater: Optional[float]) -> None:
        """Mémorise une mesure d'eau validée : secours et température maxi.

        Appelée depuis les seuls points où la filtration tourne et où le délai
        de ``sondeLocalTechniquePause`` est écoulé. Une sonde installée dans le
        local technique lit sinon de l'eau stagnante, qui ne doit ni servir de
        secours ni fausser la durée de filtration calculée.
        """

        if temperatureWater is None:
            return

        # Ecriture du secours seulement sur un ecart significatif : la sonde est
        # relue chaque minute et le Store est sauvegarde a chaque changement de
        # valeur ; memoriser le moindre dixieme userait le support de stockage
        # sans rien apporter.
        derniere = self.get_data("temperatureWaterDerniere")

        if derniere is None or abs(temperatureWater - float(derniere)) >= 0.5:
            self.set_data("temperatureWaterDerniere", temperatureWater)

        temperatureMaxi = float(self.get_data("temperatureMaxi", 0))

        if temperatureWater > temperatureMaxi:
            self.set_data("temperatureMaxi", temperatureWater)
            _LOGGER.debug(
                "temperatureMaxi: %s >> %s", temperatureMaxi, temperatureWater
            )

    def getLeverSoleil(self) -> str:
        """Récupére l'heure locale de lever du soleil au format HH:MM."""

        leverSoleilState = self.hass.states.get(self.leverSoleil)

        if leverSoleilState is None:
            _LOGGER.error("Lever du soleil %s not found", self.leverSoleil)
            return "06:00"

        # Convertir la chaîne de caractères ISO 8601 en objet datetime
        # (None si l'état n'est pas un horodatage, ex. "unavailable")
        try:
            sunriseTime = dt_util.parse_datetime(leverSoleilState.state)
        except ValueError:
            sunriseTime = None

        if sunriseTime is None:
            _LOGGER.error("Invalid sunrise value: %s", leverSoleilState.state)
            return "06:00"

        # sensor.sun_next_rising est exprimé en UTC : conversion dans le fuseau
        # de Home Assistant avant d'extraire l'heure (une valeur sans fuseau
        # est considérée comme déjà locale)
        if sunriseTime.tzinfo is not None:
            sunriseTime = dt_util.as_local(sunriseTime)

        # Convertir l'objet datetime en chaîne de caractères dans le format "06:00"
        return sunriseTime.strftime("%H:%M")

    def updateTemperatureDisplay(self, temperature: Optional[float]) -> None:
        """Met à jour l'affichage de température si l'entité existe."""

        if temperature is None:
            return

        entity_id = "input_number.temperatureDisplay"
        if self.hass.states.get(entity_id) is not None:
            self.hass.states.async_set(entity_id, temperature)
        else:
            _LOGGER.debug(
                "Temperature display entity %s not found, skipping update", entity_id
            )
