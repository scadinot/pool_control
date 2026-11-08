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
        """Mesure courante de l'eau, ou la dernière connue si la sonde est muette.

        Une sonde d'eau absente ne doit pas effacer le planning du jour : la
        dernière mesure valide prend le relais. None n'est renvoyé que si
        aucune mesure n'a jamais été vue, auquel cas le calcul est reporté.
        """

        temperatureWater = self.getTemperatureWater()
        derniere = self.get_data("temperatureWaterDerniere")

        if temperatureWater is not None:
            # Ecriture seulement sur un ecart significatif : la sonde est relue
            # chaque minute et le Store est sauvegarde a chaque changement de
            # valeur ; memoriser le moindre dixieme userait le support de
            # stockage sans rien apporter a un secours.
            if derniere is None or abs(temperatureWater - float(derniere)) >= 0.5:
                self.set_data("temperatureWaterDerniere", temperatureWater)
            return temperatureWater

        return float(derniere) if derniere is not None else None

    def recordTemperatureMaxi(self, temperatureWater: Optional[float]) -> None:
        """Mémorise la température maxi servant au prochain calcul."""

        if temperatureWater is None:
            return

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
