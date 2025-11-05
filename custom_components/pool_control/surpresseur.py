"""Surpresseur control mixin for pool automation."""

from datetime import datetime
import logging
import time
from typing import Optional

from .errors import (
    EntityNotConfiguredError,
    EntityNotFoundError,
    ServiceCallError,
)

_LOGGER = logging.getLogger(__name__)


class SurpresseurMixin:
    """Mixin providing surpresseur control methods for pool automation."""

    async def executeSurpresseurOn(self) -> None:
        """Lance le surpresseur."""

        try:
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

        except Exception as e:
            _LOGGER.exception("Unexpected error while executing surpresseur on: %s", e)
            await self._notify_error(
                "Pool Control - Surpresseur Error",
                f"Erreur lors du lancement du surpresseur: {e}",
            )

    async def refreshSurpresseur(self) -> None:
        """Rafraichi l'état du surpresseur."""

        try:
            if not self.surpresseur:
                raise EntityNotConfiguredError("surpresseur")

            surpresseurState = self.hass.states.get(self.surpresseur)

            if surpresseurState is None:
                raise EntityNotFoundError(self.surpresseur)

            if surpresseurState.state == "on":
                await self.surpresseurOn(True)
            elif surpresseurState.state == "off":
                await self.surpresseurStop(True)

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to refresh surpresseur: %s", e)
            await self._notify_error(
                "Pool Control - Surpresseur Error",
                f"Impossible de rafraîchir l'état du surpresseur: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while refreshing surpresseur: %s", e)
            await self._notify_error(
                "Pool Control - Surpresseur Error",
                f"Erreur inattendue lors du rafraîchissement du surpresseur: {e}",
            )

    def getStateSurpresseur(self) -> bool:
        """Obtient l'état du surpresseur."""

        try:
            if not self.surpresseur:
                raise EntityNotConfiguredError("surpresseur")

            surpresseurState = self.hass.states.get(self.surpresseur)

            if surpresseurState is None:
                raise EntityNotFoundError(self.surpresseur)

            return surpresseurState.state == "on"

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to get surpresseur state: %s", e)
            return False

    async def surpresseurOn(self, repeat: bool = False) -> None:
        """Active le surpresseur."""

        try:
            if not self.surpresseur:
                raise EntityNotConfiguredError("surpresseur")

            # Check current state if not repeat
            if not repeat:
                surpresseurState = self.hass.states.get(self.surpresseur)
                if surpresseurState and surpresseurState.state == "on":
                    _LOGGER.debug("Surpresseur already on, skipping")
                    return

            # Call service with error handling and state verification
            await self._safe_call_service(
                self.surpresseur, "turn_on", verify_state="on"
            )

            _LOGGER.info("Surpresseur activated successfully")

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to activate surpresseur: %s", e)
            await self._notify_error(
                "Pool Control - Surpresseur Error",
                f"Impossible d'activer le surpresseur: {e}",
            )
        except ServiceCallError as e:
            _LOGGER.error("Service call failed for surpresseur activation: %s", e)
            await self._notify_error(
                "Pool Control - Surpresseur Error",
                f"Échec de l'activation du surpresseur après plusieurs tentatives: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while activating surpresseur: %s", e)
            await self._notify_error(
                "Pool Control - Surpresseur Error",
                f"Erreur inattendue lors de l'activation du surpresseur: {e}",
            )

    async def surpresseurStop(self, repeat: bool = False) -> None:
        """Arrête le surpresseur."""

        try:
            if not self.surpresseur:
                raise EntityNotConfiguredError("surpresseur")

            # Check current state if not repeat
            if not repeat:
                surpresseurState = self.hass.states.get(self.surpresseur)
                if surpresseurState and surpresseurState.state == "off":
                    _LOGGER.debug("Surpresseur already off, skipping")
                    return

            # Call service with error handling and state verification
            await self._safe_call_service(
                self.surpresseur, "turn_off", verify_state="off"
            )

            _LOGGER.info("Surpresseur stopped successfully")

        except (EntityNotConfiguredError, EntityNotFoundError) as e:
            _LOGGER.error("Failed to stop surpresseur: %s", e)
            await self._notify_error(
                "Pool Control - Surpresseur Error",
                f"Impossible d'arrêter le surpresseur: {e}",
            )
        except ServiceCallError as e:
            _LOGGER.error("Service call failed for surpresseur stop: %s", e)
            await self._notify_error(
                "Pool Control - Surpresseur Error",
                f"Échec de l'arrêt du surpresseur après plusieurs tentatives: {e}",
            )
        except Exception as e:
            _LOGGER.exception("Unexpected error while stopping surpresseur: %s", e)
            await self._notify_error(
                "Pool Control - Surpresseur Error",
                f"Erreur inattendue lors de l'arrêt du surpresseur: {e}",
            )
