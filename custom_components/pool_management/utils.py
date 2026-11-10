"""Utility mixin for pool filtration time calculations."""

from datetime import datetime, timedelta
import logging
import time
from typing import Tuple

from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


def localDatetime(timestamp: float) -> datetime:
    """Convert a Unix timestamp to an aware datetime in Home Assistant's time zone.

    Unlike datetime.fromtimestamp(), the result does not depend on the time
    zone of the operating system (often UTC in a container).
    """

    return dt_util.as_local(dt_util.utc_from_timestamp(timestamp))


def formatTimestamp(timestamp: float, fmt: str) -> str:
    """Format a Unix timestamp in Home Assistant's time zone."""

    return localDatetime(timestamp).strftime(fmt)


def pivotTimestamp(pivot: str, flgTomorrow: bool) -> float:
    """Return the timestamp of today's HH:MM pivot in Home Assistant's time zone.

    With flgTomorrow, a pivot already passed is moved to the same wall-clock
    time on the next day, which stays correct across DST changes (unlike
    adding 24 hours).
    """

    now = localDatetime(time.time())
    pivotTime = datetime.strptime(pivot, "%H:%M").time()
    pivotDatetime = datetime.combine(now.date(), pivotTime, tzinfo=now.tzinfo)

    # la plage doit-elle etre celle de demain ?
    if flgTomorrow is True and pivotDatetime.timestamp() < time.time():
        _LOGGER.info("+1 day")
        pivotDatetime = datetime.combine(
            now.date() + timedelta(days=1), pivotTime, tzinfo=now.tzinfo
        )

    return pivotDatetime.timestamp()


def formatDurationMinutesSeconds(seconds: float) -> str:
    """Format a duration in seconds as MM:SS string.

    Unlike datetime.fromtimestamp(), this correctly handles durations
    (not absolute timestamps) and is timezone-independent.
    """

    total_seconds = max(0, int(seconds))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def formatDurationHoursMinutes(seconds: float) -> str:
    """Format a duration in seconds as HH:MM string.

    Unlike datetime.fromtimestamp(), this correctly handles durations
    (not absolute timestamps) and is timezone-independent.
    """

    total_minutes = max(0, int(seconds // 60))
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}"


class FiltrationUtilsMixin:
    """Mixin providing utility methods for pool filtration time calculations."""

    def processingTime(self, dureeHeures: float) -> Tuple[float, str]:
        """Calculate filtration time in seconds and formatted string from hours."""

        # Arrondi en minutes
        dureeHeures = int(dureeHeures * 60) / 60

        # La durée ne peut pas être supérieure à 24 H
        dureeHeures = min(dureeHeures, 24.00)

        # Conversion en secondes pour les calculs
        filtrationSecondes = dureeHeures * 3600.0

        # Conversion en hh:mm pour l'affichage
        hh = int(dureeHeures)
        mm = int((dureeHeures * 60) - (hh * 60))

        filtrationTime = f"{hh:02d}:{mm:02d}"

        return filtrationSecondes, filtrationTime

    def calculateTimeFiltrationWithCurve(self, temperatureWater: float) -> float:
        """Calculate filtration time using a cubic equation based on water temperature."""

        # Pour assurer un temps minimum de filtration, la température de calcul est forcée à 10°C
        temperature = max(temperatureWater, 10.0)

        # Coefficients de l'équation
        a = 0.00335
        b = -0.14953
        c = 2.43489
        d = -10.72859

        # Coefficient d'ajustement de la courbe (suivant config)
        coeff = self.coefficientAjustement

        a *= coeff
        b *= coeff
        c *= coeff
        d *= coeff

        return (
            (a * pow(temperature, 3))
            + (b * pow(temperature, 2))
            + (c * temperature)
            + d
        )

    def calculateTimeFiltrationWithTemperatureReducedByHalf(self, temperatureWater: float) -> float:
        """Calculate filtration time using a simplified method based on water temperature."""

        # Calcul simplifié
        dureeHeures = temperatureWater / 2.0

        # Coefficient d'ajustement (suivant config)
        dureeHeures *= self.coefficientAjustement

        return dureeHeures

    def calculateTimeFiltrationWithTemperatureHivernage(self, temperatureWater: float) -> float:
        """Calculate filtration time for winter mode based on water temperature."""

        # Filtration (temperature / 3)
        dureeHeures = temperatureWater / 3.0

        # Coefficient d'ajustement (suivant config)
        dureeHeures *= self.coefficientAjustementHivernage

        # Au moins 3 heures
        return max(dureeHeures, self.tempsDeFiltrationMinimum)
