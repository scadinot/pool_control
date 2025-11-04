"""Scheduler mixin for pool control integration."""

from datetime import datetime, timedelta
import logging
import time
from typing import Any, Optional

from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)


class SchedulerMixin:
    """Scheduler mixin for pool control integration."""

    def __init__(self):
        """Initialize the SchedulerMixin with default values."""

        self.secondCronCancel = None

        # Propriétés de l'objet
        self.filtrationRefreshCounter = 0

    async def startSecondCron(self) -> None:
        """Lance le cron '5 secondes'."""

        if self.secondCronCancel is not None:
            self.secondCronCancel()

        # Call 'pull' method every 5 secondes
        self.secondCronCancel = async_track_time_interval(
            self.hass, self.pull, timedelta(seconds=5)
        )

        _LOGGER.info("Second cron job started")

    async def stopSecondCron(self) -> None:
        """Arrete le cron '5 secondes'."""

        if self.secondCronCancel is not None:
            self.secondCronCancel()
            self.secondCronCancel = None

            _LOGGER.info("Second cron job stopped")

    async def pull(self, now: Optional[Any] = None) -> None:
        """Routine toutes les 5 secondes pour suivi du lavage et surpresseur."""

        _LOGGER.debug("pull() begin")

        if int(self.get_data("filtrationSurpresseur", 0)) == 1:
            timeFin = self.get_data("filtrationTempsRestant", 0)
            timeRestant = timeFin - time.time()

            if timeRestant > 0:
                display = (
                    f"Actif : {datetime.fromtimestamp(timeRestant).strftime('%M:%S')}"
                )
                if self.surpresseurStatus:
                    self.surpresseurStatus.set_status(display)
            else:
                await self.executeButtonStop()

        if int(self.get_data("filtrationLavageEtat", 0)) in [2, 4]:
            label = (
                "Lavage" if self.get_data("filtrationLavageEtat", 0) == 2 else "Rinçage"
            )
            timeFin = self.get_data("filtrationTempsRestant", 0)
            timeRestant = timeFin - time.time()

            if timeRestant > 0:
                display = (
                    f"{label} : {datetime.fromtimestamp(timeRestant).strftime('%M:%S')}"
                )
                if self.filtreSableLavageStatus:
                    self.filtreSableLavageStatus.set_status(display)
            else:
                await self.executeFiltreSableLavageOn()

        _LOGGER.debug("pull() end")

    async def startFirstCron(self) -> None:
        """Lance le cron '1 minute'."""

        async_track_time_interval(self.hass, self.cron, timedelta(minutes=1))

        _LOGGER.info("First cron job started")

    async def cron(self, now: Optional[Any] = None) -> None:
        """Routine toutes les minutes : suivi de la filtration, hivernage, traitements..."""

        _LOGGER.debug("cron() begin")

        temperatureWater = self.getTemperatureWater()
        temperatureOutdoor = self.getTemperatureOutdoor()
        # leverSoleil = self.getLeverSoleil()

        ###########################################################################################

        if self.filtrationRefreshCounter >= 5:
            # Refresh appellé toutes les 5 minutes

            _LOGGER.info(
                "Time = %s",
                datetime.fromtimestamp(time.time()).strftime("%H:%M %d-%m-%Y"),
            )

            # _LOGGER.info(f"temperatureWater={temperatureWater}")
            # _LOGGER.info(f"temperatureOutdoor={temperatureOutdoor}")
            # _LOGGER.info(f"leverSoleil={leverSoleil}")

            await self.refreshFiltration()
            await self.refreshSurpresseur()
            if self.traitement:
                await self.refreshTraitement()
            if self.traitement_2:
                await self.refreshTraitement_2()

            self.filtrationRefreshCounter = 0
        else:
            self.filtrationRefreshCounter += 1

        if self.getHivernage():
            await self.calculateStatusFiltrationHivernage(
                temperatureWater, temperatureOutdoor
            )
        else:
            await self.calculateStatusFiltration(temperatureWater)

        ###########################################################################################

        await self.activatingDevices()

        ###########################################################################################

        _LOGGER.debug("cron() end")
