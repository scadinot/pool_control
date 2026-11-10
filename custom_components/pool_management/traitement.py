"""Traitement mixin for pool control integration."""

import logging

_LOGGER = logging.getLogger(__name__)


class TraitementMixin:
    """Mixin providing treatment control methods for pool automation."""

    async def refreshTraitement(self) -> None:
        """Rafraichi l'état du traitement."""

        if not self.traitement:
            _LOGGER.error("Traitement entity ID is not configured.")
            return

        traitementState = self.hass.states.get(self.traitement)

        if traitementState is None:
            _LOGGER.error("Traitement %s not found", self.traitement)
            return

        if traitementState.state == "on":
            await self.traitementOn(True)

        elif traitementState.state == "off":
            await self.traitementStop(True)

        return

    def getStateTraitement(self) -> bool:
        """Obtient l'état du traitement."""

        if not self.traitement:
            _LOGGER.error("Traitement entity ID is not configured.")
            return False

        traitementState = self.hass.states.get(self.traitement)

        if traitementState is None:
            _LOGGER.error("Traitement %s not found", self.traitement)
            return False

        if traitementState.state == "on":
            return True
        return False

    async def traitementOn(self, repeat: bool = False) -> None:
        """Active le traitement."""

        if not self.traitement:
            _LOGGER.error("Traitement entity ID is not configured.")
            return

        traitementState = self.hass.states.get(self.traitement)

        if traitementState is None:
            _LOGGER.error("Traitement %s not found", self.traitement)
            return

        if not repeat and traitementState.state == "on":
            return

        # Active le traitement
        await self._safe_service_call(
            domain=self.traitement.split(".")[0],
            service="turn_on",
            service_data={"entity_id": self.traitement},
            entity_name="traitement",
        )

        return

    async def traitementStop(self, repeat: bool = False) -> None:
        """Arrête le traitement."""

        if not self.traitement:
            _LOGGER.error("Traitement entity ID is not configured.")
            return

        traitementState = self.hass.states.get(self.traitement)

        if traitementState is None:
            _LOGGER.error("Traitement %s not found", self.traitement)
            return

        if not repeat and traitementState.state == "off":
            return

        # Arrête le traitement
        await self._safe_service_call(
            domain=self.traitement.split(".")[0],
            service="turn_off",
            service_data={"entity_id": self.traitement},
            entity_name="traitement",
        )

        return

    ## Traitement 2

    async def refreshTraitement_2(self) -> None:
        """Rafraichi l'état du traitement_2."""

        if not self.traitement_2:
            _LOGGER.error("Traitement_2 entity ID is not configured.")
            return

        traitementState = self.hass.states.get(self.traitement_2)

        if traitementState is None:
            _LOGGER.error("Traitement %s not found", self.traitement_2)
            return

        if traitementState.state == "on":
            await self.traitement_2_On(True)

        elif traitementState.state == "off":
            await self.traitement_2_Stop(True)

        return

    def getStateTraitement_2(self) -> bool:
        """Obtient l'état du traitement."""

        if not self.traitement_2:
            _LOGGER.error("Traitement_2 entity ID is not configured.")
            return False

        traitementState = self.hass.states.get(self.traitement_2)

        if traitementState is None:
            _LOGGER.error("Traitement %s not found", self.traitement_2)
            return False

        if traitementState.state == "on":
            return True
        return False

    async def traitement_2_On(self, repeat: bool = False) -> None:
        """Active le traitement."""

        if not self.traitement_2:
            _LOGGER.error("Traitement_2 entity ID is not configured.")
            return

        traitementState = self.hass.states.get(self.traitement_2)

        if traitementState is None:
            _LOGGER.error("Traitement %s not found", self.traitement_2)
            return

        if not repeat and traitementState.state == "on":
            return

        # Active le traitement
        await self._safe_service_call(
            domain=self.traitement_2.split(".")[0],
            service="turn_on",
            service_data={"entity_id": self.traitement_2},
            entity_name="traitement_2",
        )

        return

    async def traitement_2_Stop(self, repeat: bool = False) -> None:
        """Arrête le traitement."""

        if not self.traitement_2:
            _LOGGER.error("Traitement_2 entity ID is not configured.")
            return

        traitementState = self.hass.states.get(self.traitement_2)

        if traitementState is None:
            _LOGGER.error("Traitement %s not found", self.traitement_2)
            return

        if not repeat and traitementState.state == "off":
            return

        # Arrête le traitement
        await self._safe_service_call(
            domain=self.traitement_2.split(".")[0],
            service="turn_off",
            service_data={"entity_id": self.traitement_2},
            entity_name="traitement_2",
        )

        return
