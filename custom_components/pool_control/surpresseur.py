"""Surpresseur control mixin for pool automation."""

from datetime import datetime
import logging
import time

_LOGGER = logging.getLogger(__name__)


class SurpresseurMixin:
    """Mixin providing surpresseur control methods for pool automation."""

    async def executeSurpresseurOn(self):
        """Lance le surpresseur."""

        if (
            int(self.get_data("filtrationSurpresseur", 0)) == 0
            and int(self.get_data("filtrationLavageEtat", 0)) == 0
        ):
            timeFin = time.time() + (self.surpresseurDuree * 60)
            self.set_data("filtrationTempsRestant", int(timeFin))

            timeRestant = timeFin - time.time()
            display = "Actif"
            display += " : "
            display += datetime.fromtimestamp(timeRestant).strftime("%M:%S")
            if self.surpresseurStatus:
                self.surpresseurStatus.set_status(display)

            self.set_data("filtrationSurpresseur", 1)
            await self.activatingDevices()

        await self.startSecondCron()

    async def refreshSurpresseur(self):
        """Rafraichi l'état du surpresseur."""

        if not self.surpresseur:
            _LOGGER.error("Surpresseur entity ID is not configured.")
            return

        surpresseurState = self.hass.states.get(self.surpresseur)

        if surpresseurState is None:
            _LOGGER.error("Surpresseur %s not found", self.surpresseur)
            return

        if surpresseurState.state == "on":
            await self.surpresseurOn(True)

        elif surpresseurState.state == "off":
            await self.surpresseurStop(True)

        return

    def getStateSurpresseur(self) -> bool:
        """Obtient l'état du surpresseur."""

        if not self.surpresseur:
            _LOGGER.error("Surpresseur entity ID is not configured.")
            return False

        surpresseurState = self.hass.states.get(self.surpresseur)

        if surpresseurState is None:
            _LOGGER.error("Surpresseur %s not found", self.surpresseur)
            return False

        if surpresseurState.state == "on":
            return True
        return False

    async def surpresseurOn(self, repeat=False):
        """Active le surpresseur."""

        if not self.surpresseur:
            _LOGGER.error("Surpresseur entity ID is not configured.")
            return

        surpresseurState = self.hass.states.get(self.surpresseur)

        if surpresseurState is None:
            _LOGGER.error("Surpresseur %s not found", self.surpresseur)
            return

        if not repeat and surpresseurState.state == "on":
            return

        # Active le surpresseur
        await self.hass.services.async_call(
            self.surpresseur.split(".")[0],
            "turn_on",
            {"entity_id": self.surpresseur},
        )

        # if self.surpresseurStatus:
        #    self.surpresseurStatus.set_status("Actif")

        return

    async def surpresseurStop(self, repeat=False):
        """Arrête le surpresseur."""

        if not self.surpresseur:
            _LOGGER.error("Surpresseur entity ID is not configured.")
            return

        surpresseurState = self.hass.states.get(self.surpresseur)

        if surpresseurState is None:
            _LOGGER.error("Surpresseur %s not found", self.surpresseur)
            return

        if not repeat and surpresseurState.state == "off":
            return

        # Arrête le surpresseur
        await self.hass.services.async_call(
            self.surpresseur.split(".")[0],
            "turn_off",
            {"entity_id": self.surpresseur},
        )

        # if self.surpresseurStatus:
        #   self.surpresseurStatus.set_status("Arrêté")

        return
