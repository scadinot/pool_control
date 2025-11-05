"""Traitement mixin for pool control integration."""

import logging
from typing import Optional

from .errors import (
    EntityNotConfiguredError,
    EntityNotFoundError,
    ServiceCallError,
)

_LOGGER = logging.getLogger(__name__)


class TraitementMixin:
    """Mixin providing treatment control methods for pool automation."""

    async def refreshTraitement(self) -> None:
        """Rafraichi l'état du traitement."""

        try:
            if not self.traitement:
                raise EntityNotConfiguredError("traitement")

            traitementState = self.hass.states.get(self.traitement)

            if traitementState is None:
                raise EntityNotFoundError(self.traitement)

            if traitementState.state == "on":
                await self.traitementOn(True)
            elif traitementState.state == "off":
                await self.traitementStop(True)

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to refresh traitement: %s", e)
            await self._notify_error(
                "Pool Control - Traitement Error",
                f"Impossible de rafraîchir l'état du traitement: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while refreshing traitement: %s", e)
            await self._notify_error(
                "Pool Control - Traitement Error",
                f"Erreur inattendue lors du rafraîchissement du traitement: {e}",
            )

    def getStateTraitement(self) -> bool:
        """Obtient l'état du traitement."""

        try:
            if not self.traitement:
                raise EntityNotConfiguredError("traitement")

            traitementState = self.hass.states.get(self.traitement)

            if traitementState is None:
                raise EntityNotFoundError(self.traitement)

            return traitementState.state == "on"

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to get traitement state: %s", e)
            return False

    async def traitementOn(self, repeat: bool = False) -> None:
        """Active le traitement."""

        try:
            if not self.traitement:
                raise EntityNotConfiguredError("traitement")

            # Check current state if not repeat
            if not repeat:
                traitementState = self.hass.states.get(self.traitement)
                if traitementState and traitementState.state == "on":
                    _LOGGER.debug("Traitement already on, skipping")
                    return

            # Call service with error handling and state verification
            await self._safe_call_service(
                self.traitement, "turn_on", verify_state="on"
            )

            _LOGGER.info("Traitement activated successfully")

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to activate traitement: %s", e)
            await self._notify_error(
                "Pool Control - Traitement Error",
                f"Impossible d'activer le traitement: {e}",
            )
        except ServiceCallError as e:
            _LOGGER.error("Service call failed for traitement activation: %s", e)
            await self._notify_error(
                "Pool Control - Traitement Error",
                f"Échec de l'activation du traitement après plusieurs tentatives: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while activating traitement: %s", e)
            await self._notify_error(
                "Pool Control - Traitement Error",
                f"Erreur inattendue lors de l'activation du traitement: {e}",
            )

    async def traitementStop(self, repeat: bool = False) -> None:
        """Arrête le traitement."""

        try:
            if not self.traitement:
                raise EntityNotConfiguredError("traitement")

            # Check current state if not repeat
            if not repeat:
                traitementState = self.hass.states.get(self.traitement)
                if traitementState and traitementState.state == "off":
                    _LOGGER.debug("Traitement already off, skipping")
                    return

            # Call service with error handling and state verification
            await self._safe_call_service(
                self.traitement, "turn_off", verify_state="off"
            )

            _LOGGER.info("Traitement stopped successfully")

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to stop traitement: %s", e)
            await self._notify_error(
                "Pool Control - Traitement Error",
                f"Impossible d'arrêter le traitement: {e}",
            )
        except ServiceCallError as e:
            _LOGGER.error("Service call failed for traitement stop: %s", e)
            await self._notify_error(
                "Pool Control - Traitement Error",
                f"Échec de l'arrêt du traitement après plusieurs tentatives: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while stopping traitement: %s", e)
            await self._notify_error(
                "Pool Control - Traitement Error",
                f"Erreur inattendue lors de l'arrêt du traitement: {e}",
            )

    ## Traitement 2

    async def refreshTraitement_2(self) -> None:
        """Rafraichi l'état du traitement_2."""

        try:
            if not self.traitement_2:
                raise EntityNotConfiguredError("traitement_2")

            traitementState = self.hass.states.get(self.traitement_2)

            if traitementState is None:
                raise EntityNotFoundError(self.traitement_2)

            if traitementState.state == "on":
                await self.traitement_2_On(True)
            elif traitementState.state == "off":
                await self.traitement_2_Stop(True)

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to refresh traitement_2: %s", e)
            await self._notify_error(
                "Pool Control - Traitement 2 Error",
                f"Impossible de rafraîchir l'état du traitement 2: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while refreshing traitement_2: %s", e)
            await self._notify_error(
                "Pool Control - Traitement 2 Error",
                f"Erreur inattendue lors du rafraîchissement du traitement 2: {e}",
            )

    def getStateTraitement_2(self) -> bool:
        """Obtient l'état du traitement_2."""

        try:
            if not self.traitement_2:
                raise EntityNotConfiguredError("traitement_2")

            traitementState = self.hass.states.get(self.traitement_2)

            if traitementState is None:
                raise EntityNotFoundError(self.traitement_2)

            return traitementState.state == "on"

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to get traitement_2 state: %s", e)
            return False

    async def traitement_2_On(self, repeat: bool = False) -> None:
        """Active le traitement 2."""

        try:
            if not self.traitement_2:
                raise EntityNotConfiguredError("traitement_2")

            # Check current state if not repeat
            if not repeat:
                traitementState = self.hass.states.get(self.traitement_2)
                if traitementState and traitementState.state == "on":
                    _LOGGER.debug("Traitement_2 already on, skipping")
                    return

            # Call service with error handling and state verification
            await self._safe_call_service(
                self.traitement_2, "turn_on", verify_state="on"
            )

            _LOGGER.info("Traitement_2 activated successfully")

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to activate traitement_2: %s", e)
            await self._notify_error(
                "Pool Control - Traitement 2 Error",
                f"Impossible d'activer le traitement 2: {e}",
            )
        except ServiceCallError as e:
            _LOGGER.error("Service call failed for traitement_2 activation: %s", e)
            await self._notify_error(
                "Pool Control - Traitement 2 Error",
                f"Échec de l'activation du traitement 2 après plusieurs tentatives: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while activating traitement_2: %s", e)
            await self._notify_error(
                "Pool Control - Traitement 2 Error",
                f"Erreur inattendue lors de l'activation du traitement 2: {e}",
            )

    async def traitement_2_Stop(self, repeat: bool = False) -> None:
        """Arrête le traitement 2."""

        try:
            if not self.traitement_2:
                raise EntityNotConfiguredError("traitement_2")

            # Check current state if not repeat
            if not repeat:
                traitementState = self.hass.states.get(self.traitement_2)
                if traitementState and traitementState.state == "off":
                    _LOGGER.debug("Traitement_2 already off, skipping")
                    return

            # Call service with error handling and state verification
            await self._safe_call_service(
                self.traitement_2, "turn_off", verify_state="off"
            )

            _LOGGER.info("Traitement_2 stopped successfully")

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to stop traitement_2: %s", e)
            await self._notify_error(
                "Pool Control - Traitement 2 Error",
                f"Impossible d'arrêter le traitement 2: {e}",
            )
        except ServiceCallError as e:
            _LOGGER.error("Service call failed for traitement_2 stop: %s", e)
            await self._notify_error(
                "Pool Control - Traitement 2 Error",
                f"Échec de l'arrêt du traitement 2 après plusieurs tentatives: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while stopping traitement_2: %s", e)
            await self._notify_error(
                "Pool Control - Traitement 2 Error",
                f"Erreur inattendue lors de l'arrêt du traitement 2: {e}",
            )
