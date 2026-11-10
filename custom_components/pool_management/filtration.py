"""Filtration control mixin for pool automation."""

import logging

_LOGGER = logging.getLogger(__name__)


class FiltrationMixin:
    """Mixin providing filtration control methods for pool automation."""

    async def refreshFiltration(self) -> None:
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

    async def filtrationOn(self, repeat: bool = False) -> None:
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
        success = await self._safe_service_call(
            domain=self.filtration.split(".")[0],
            service="turn_on",
            service_data={"entity_id": self.filtration},
            entity_name="filtration",
        )

        if success and self.filtrationStatus:
            self.filtrationStatus.set_status("Actif")

        return

    async def filtrationStop(self, repeat: bool = False) -> None:
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
        success = await self._safe_service_call(
            domain=self.filtration.split(".")[0],
            service="turn_off",
            service_data={"entity_id": self.filtration},
            entity_name="filtration",
        )

        if success and self.filtrationStatus:
            self.filtrationStatus.set_status("Arrêté")

        return
