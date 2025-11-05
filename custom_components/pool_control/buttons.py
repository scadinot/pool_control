"""Button handlers for pool control integration."""

from datetime import datetime
import logging
import time
from typing import Any

from .errors import PoolControlError

_LOGGER = logging.getLogger(__name__)


class ButtonMixin:
    """Mixin class providing button handler methods for pool control."""

    async def executeButtonStop(self) -> None:
        """Arrête le surpresseur / lavage filtre."""

        try:
            await self.stopSecondCron()

            if int(self.get_data("filtrationSurpresseur", 0)) == 1:
                self.set_data("filtrationSurpresseur", 0)
                if self.surpresseurStatus:
                    self.surpresseurStatus.set_status("Arrêté")
                await self.activatingDevices()

            if int(self.get_data("filtrationLavageEtat", 0)) != 0:
                self.set_data("filtrationLavageEtat", 0)
                self.set_data("filtrationLavage", 0)
                if self.filtreSableLavageStatus:
                    self.filtreSableLavageStatus.set_status("Arrêté")
                await self.activatingDevices()

        except PoolControlError as e:
            _LOGGER.error("Pool control error during button stop: %s", e)
        except Exception as e:
            _LOGGER.exception("Unexpected error during button stop: %s", e)
            await self._notify_error(
                "Pool Control - Button Error",
                f"Erreur lors de l'exécution du bouton Stop: {e}",
            )

    async def executeButtonReset(self) -> None:
        """Reinitialise le calcul."""

        try:
            if self.getHivernage() is True:
                self.set_data("temperatureMaxi", 0)  # reset temperature maxi

                temperatureWater = self.getTemperatureWater()
                temperatureOutdoor = self.getTemperatureOutdoor()

                self.calculateTimeFiltrationHivernage(temperatureWater, False)

                # Verifie si la plage calculée est passée
                filtrationFin = self.get_data("filtrationFin", 0)
                timeNow = time.time()

                _LOGGER.debug(
                    "filtrationFin=%s",
                    datetime.fromtimestamp(filtrationFin).strftime("%H:%M %d-%m-%Y"),
                )
                _LOGGER.info(
                    "timeNow=%s",
                    datetime.fromtimestamp(time.time()).strftime("%H:%M %d-%m-%Y"),
                )

                if timeNow > filtrationFin:
                    # On est apres la plage de filtration, relancer le calcul pour la plage de demain
                    self.calculateTimeFiltrationHivernage(temperatureWater, True)

                await self.calculateStatusFiltrationHivernage(
                    temperatureWater, temperatureOutdoor
                )

            else:
                self.set_data("temperatureMaxi", 0)  # reset temperature maxi

                temperatureWater = self.getTemperatureWater()
                self.calculateTimeFiltration(temperatureWater, False)

                # Verifie si la plage calculée est passée
                filtrationFin = self.get_data("filtrationFin", 0)
                timeNow = time.time()

                _LOGGER.debug(
                    "filtrationFin=%s",
                    datetime.fromtimestamp(filtrationFin).strftime("%H:%M %d-%m-%Y"),
                )
                _LOGGER.info(
                    "timeNow=%s",
                    datetime.fromtimestamp(time.time()).strftime("%H:%M %d-%m-%Y"),
                )

                if timeNow > filtrationFin:
                    # On est apres la plage de filtration, relancer le calcul pour la plage de demain
                    self.calculateTimeFiltration(temperatureWater, True)

                await self.calculateStatusFiltration(temperatureWater)

            await self.activatingDevices()

        except PoolControlError as e:
            _LOGGER.error("Pool control error during button reset: %s", e)
        except Exception as e:
            _LOGGER.exception("Unexpected error during button reset: %s", e)
            await self._notify_error(
                "Pool Control - Button Error",
                f"Erreur lors de l'exécution du bouton Reset: {e}",
            )

    async def executeButtonActif(self) -> None:
        """Lance le surpresseur / lavage filtre."""

        try:
            self.set_data("marcheForcee", 1)
            self.set_data("arretTotal", 0)
            await self.activatingDevices()
        except Exception as e:
            _LOGGER.exception("Unexpected error during button actif: %s", e)
            await self._notify_error(
                "Pool Control - Button Error",
                f"Erreur lors de l'exécution du bouton Actif: {e}",
            )

    async def executeButtonAuto(self) -> None:
        """Lance le surpresseur / lavage filtre."""

        try:
            self.set_data("marcheForcee", 0)
            self.set_data("arretTotal", 0)
            await self.activatingDevices()
        except Exception as e:
            _LOGGER.exception("Unexpected error during button auto: %s", e)
            await self._notify_error(
                "Pool Control - Button Error",
                f"Erreur lors de l'exécution du bouton Auto: {e}",
            )

    async def executeButtonInactif(self) -> None:
        """Arrête le surpresseur / lavage filtre."""

        try:
            self.set_data("marcheForcee", 0)
            self.set_data("arretTotal", 1)
            await self.activatingDevices()
        except Exception as e:
            _LOGGER.exception("Unexpected error during button inactif: %s", e)
            await self._notify_error(
                "Pool Control - Button Error",
                f"Erreur lors de l'exécution du bouton Inactif: {e}",
            )

    async def executeButtonSaison(self) -> None:
        """Lance le surpresseur / lavage filtre."""

        try:
            self.set_data("hivernageWidgetStatus", 0)
            await self.activatingDevices()
            await self.executeButtonReset()
        except Exception as e:
            _LOGGER.exception("Unexpected error during button saison: %s", e)
            await self._notify_error(
                "Pool Control - Button Error",
                f"Erreur lors de l'exécution du bouton Saison: {e}",
            )

    async def executeButtonHivernage(self) -> None:
        """Arrête le surpresseur / lavage filtre."""

        try:
            self.set_data("hivernageWidgetStatus", 1)
            await self.activatingDevices()
            await self.executeButtonReset()
        except Exception as e:
            _LOGGER.exception("Unexpected error during button hivernage: %s", e)
            await self._notify_error(
                "Pool Control - Button Error",
                f"Erreur lors de l'exécution du bouton Hivernage: {e}",
            )
