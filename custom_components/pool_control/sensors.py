"""Sensor mixin for Pool Control integration."""

from datetime import datetime
import logging

_LOGGER = logging.getLogger(__name__)


class SensorMixin:
    """Mixin class providing sensor methods for Pool Control integration."""

    def getTemperatureWater(self) -> float:
        """Récupére la température de l'eau."""

        temperatureWaterState = self.hass.states.get(self.temperatureWater)

        if temperatureWaterState is None:
            _LOGGER.error("Temperature water %s not found", self.temperatureWater)
            return 0.0

        try:
            temperatureWater = float(temperatureWaterState.state)
        except ValueError:
            _LOGGER.error("Invalid temperature value: %s", temperatureWaterState.state)
            return 0.0

        return temperatureWater

    def getTemperatureOutdoor(self) -> float:
        """Récupére la température de l'air."""

        temperatureOutdoorState = self.hass.states.get(self.temperatureOutdoor)

        if temperatureOutdoorState is None:
            _LOGGER.error("Temperature air %s not found", self.temperatureOutdoor)
            return 0.0

        try:
            temperatureOutdoor = float(temperatureOutdoorState.state)
        except ValueError:
            _LOGGER.error(
                "Invalid temperature value: %s", temperatureOutdoorState.state
            )
            return 0.0

        return temperatureOutdoor

    def getLeverSoleil(self) -> str:
        """Récupére l'heure de lever du soleil."""

        leverSoleilState = self.hass.states.get(self.leverSoleil)

        if leverSoleilState is None:
            _LOGGER.error("Lever du soleil %s not found", self.leverSoleil)
            return "06:00"

        # Extraire l'heure de lever du soleil à partir de l'état
        sunriseTimeStr = leverSoleilState.state

        # Convertir la chaîne de caractères ISO 8601 en objet datetime
        sunriseTime = datetime.fromisoformat(sunriseTimeStr)

        # Convertir l'objet datetime en chaîne de caractères dans le format "06:00"
        return sunriseTime.strftime("%H:%M")
