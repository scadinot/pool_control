"""Filtration control mixin for pool automation."""

import logging
from typing import Optional

from .errors import (
    EntityNotConfiguredError,
    EntityNotFoundError,
    ServiceCallError,
)

_LOGGER = logging.getLogger(__name__)


class FiltrationMixin:
    """Mixin providing filtration control methods for pool automation."""

    async def refreshFiltration(self) -> None:
        """Rafraichi l'état de la filtration."""

        try:
            if not self.filtration:
                raise EntityNotConfiguredError("filtration")

            filtrationState = self.hass.states.get(self.filtration)

            if filtrationState is None:
                raise EntityNotFoundError(self.filtration)

            if filtrationState.state == "on":
                await self.filtrationOn(True)
            elif filtrationState.state == "off":
                await self.filtrationStop(True)

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            # Configuration errors - log only, no user notification
            _LOGGER.error("Failed to refresh filtration: %s", e)
        except Exception as e:
            _LOGGER.exception("Unexpected error while refreshing filtration: %s", e)
            await self._notify_error(
                "Pool Control - Filtration Error",
                f"Erreur inattendue lors du rafraîchissement de la filtration: {e}",
            )

    async def filtrationOn(self, repeat: bool = False) -> None:
        """Active la filtration."""

        try:
            if not self.filtration:
                raise EntityNotConfiguredError("filtration")

            # Check current state if not repeat
            if not repeat:
                filtrationState = self.hass.states.get(self.filtration)
                if filtrationState and filtrationState.state == "on":
                    _LOGGER.debug("Filtration already on, skipping")
                    return

            # Call service with error handling and state verification
            await self._safe_call_service(
                self.filtration, "turn_on", verify_state="on"
            )

            # Update status display
            if self.filtrationStatus:
                self.filtrationStatus.set_status("Actif")

            _LOGGER.info("Filtration activated successfully")

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            # Configuration errors - log only, no user notification
            _LOGGER.error("Failed to activate filtration: %s", e)
        except ServiceCallError as e:
            _LOGGER.error("Service call failed for filtration activation: %s", e)
            await self._notify_error(
                "Pool Control - Filtration Error",
                f"Échec de l'activation de la filtration après plusieurs tentatives: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while activating filtration: %s", e)
            await self._notify_error(
                "Pool Control - Filtration Error",
                f"Erreur inattendue lors de l'activation de la filtration: {e}",
            )

    async def filtrationStop(self, repeat: bool = False) -> None:
        """Arrête la filtration."""

        try:
            if not self.filtration:
                raise EntityNotConfiguredError("filtration")

            # Check current state if not repeat
            if not repeat:
                filtrationState = self.hass.states.get(self.filtration)
                if filtrationState and filtrationState.state == "off":
                    _LOGGER.debug("Filtration already off, skipping")
                    return

            # Call service with error handling and state verification
            await self._safe_call_service(
                self.filtration, "turn_off", verify_state="off"
            )

            # Update status display
            if self.filtrationStatus:
                self.filtrationStatus.set_status("Arrêté")

            _LOGGER.info("Filtration stopped successfully")

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            # Configuration errors - log only, no user notification
            _LOGGER.error("Failed to stop filtration: %s", e)
        except ServiceCallError as e:
            _LOGGER.error("Service call failed for filtration stop: %s", e)
            await self._notify_error(
                "Pool Control - Filtration Error",
                f"Échec de l'arrêt de la filtration après plusieurs tentatives: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while stopping filtration: %s", e)
            await self._notify_error(
                "Pool Control - Filtration Error",
                f"Erreur inattendue lors de l'arrêt de la filtration: {e}",
            )
