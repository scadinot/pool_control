"""Utility mixin for pool filtration time calculations."""

from typing import Tuple


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
