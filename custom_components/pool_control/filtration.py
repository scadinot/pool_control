"""Filtration control mixin for pool automation."""

import logging

_LOGGER = logging.getLogger(__name__)


class FiltrationMixin:
    """Mixin providing filtration control methods for pool automation."""

    async def refreshFiltration(self):
        """Rafraichi l'état de la filtration."""

        if not self.filtration:
            _LOGGER.error("Filtration entity ID is not configured.")
            return

        filtrationState = self.hass.states.get(self.filtration)

        if filtrationState is None:
            _LOGGER.error("Filtration %s not found", self.filtration)
            return

        if filtrationState.state == "on":
            await self.filtrationOn(True)

        elif filtrationState.state == "off":
            await self.filtrationStop(True)

        return

    async def filtrationOn(self, repeat=False):
        """Active la filtration."""

        if not self.filtration:
            _LOGGER.error("Filtration entity ID is not configured.")
            return

        filtrationState = self.hass.states.get(self.filtration)

        if filtrationState is None:
            _LOGGER.error("Filtration %s not found", self.filtration)
            return

        if not repeat and filtrationState.state == "on":
            return

        # Active la filtration
        await self.hass.services.async_call(
            self.filtration.split(".")[0],
            "turn_on",
            {"entity_id": self.filtration},
        )

        if self.filtrationStatus:
            self.filtrationStatus.set_status("Actif")

        return

    async def filtrationStop(self, repeat=False):
        """Arrête la filtration."""

        if not self.filtration:
            _LOGGER.error("Filtration entity ID is not configured.")
            return

        filtrationState = self.hass.states.get(self.filtration)

        if filtrationState is None:
            _LOGGER.error("Filtration %s not found", self.filtration)
            return

        if not repeat and filtrationState.state == "off":
            return

        # Arrête la filtration
        await self.hass.services.async_call(
            self.filtration.split(".")[0],
            "turn_off",
            {"entity_id": self.filtration},
        )

        if self.filtrationStatus:
            self.filtrationStatus.set_status("Arrêté")

        return
