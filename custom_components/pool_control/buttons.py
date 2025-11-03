"""Button handlers for pool control integration."""

from datetime import datetime
import logging
import time
from typing import Any

_LOGGER = logging.getLogger(__name__)


class ButtonMixin:
    """Mixin class providing button handler methods for pool control."""

    async def executeButtonStop(self) -> None:
        """Arrête le surpresseur / lavage filtre."""

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

    async def executeButtonReset(self) -> None:
        """Reinitialise le calcul."""

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

    async def executeButtonActif(self) -> None:
        """Lance le surpresseur / lavage filtre."""

        self.set_data("marcheForcee", 1)
        self.set_data("arretTotal", 0)
        await self.activatingDevices()

    async def executeButtonAuto(self) -> None:
        """Lance le surpresseur / lavage filtre."""

        self.set_data("marcheForcee", 0)
        self.set_data("arretTotal", 0)
        await self.activatingDevices()

    async def executeButtonInactif(self) -> None:
        """Arrête le surpresseur / lavage filtre."""

        self.set_data("marcheForcee", 0)
        self.set_data("arretTotal", 1)
        await self.activatingDevices()

    async def executeButtonSaison(self) -> None:
        """Lance le surpresseur / lavage filtre."""

        self.set_data("hivernageWidgetStatus", 0)
        await self.activatingDevices()
        await self.executeButtonReset()

    async def executeButtonHivernage(self) -> None:
        """Arrête le surpresseur / lavage filtre."""

        self.set_data("hivernageWidgetStatus", 1)
        await self.activatingDevices()
        await self.executeButtonReset()
