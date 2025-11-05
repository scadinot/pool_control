"""Activation logic for pool control devices."""

import asyncio
import logging
from typing import Optional

from .errors import PoolControlError

_LOGGER = logging.getLogger(__name__)

# Constants for delays
DEVICE_ACTIVATION_DELAY = 2  # seconds


class ActivationMixin:
    """Mixin for activation logic of pool control devices."""

    async def activatingDevices(self) -> None:
        """Active les appareils de filtration et de traitement."""

        _LOGGER.debug("activatingDevices() begin")

        try:
            # Update status display
            self._update_status_display()

            # Handle device activation based on current mode
            if int(self.get_data("arretTotal", 0)) == 0:
                await self._handle_active_mode()
            else:
                await self._handle_stop_all()

            _LOGGER.debug("activatingDevices() end")

        except PoolControlError as e:
            _LOGGER.error("Pool control error during device activation: %s", e)
            # Error already notified by individual methods
        except Exception as e:
            _LOGGER.exception("Unexpected error during device activation: %s", e)
            await self._notify_error(
                "Pool Control - Activation Error",
                f"Erreur inattendue lors de l'activation des dispositifs: {e}",
            )

    def _update_status_display(self) -> None:
        """Update the status display based on current state."""

        if int(self.get_data("arretTotal", 0)) == 0:
            if int(self.get_data("marcheForcee", 0)) == 1:
                status = "Actif"
            else:
                status = "Auto"
        else:
            status = "Inactif"

        status = self.getStatusHivernage(status)
        if self.asservissementStatus:
            self.asservissementStatus.set_status(status)

    async def _handle_active_mode(self) -> None:
        """Handle device activation when not in total stop mode."""

        filtration_lavage = int(self.get_data("filtrationLavage", 0))

        if filtration_lavage == 0:
            await self._handle_normal_filtration_mode()
        elif filtration_lavage == 1:
            await self._handle_lavage_stop_mode()
        elif filtration_lavage == 2:
            await self._handle_lavage_filtration_mode()

    async def _handle_normal_filtration_mode(self) -> None:
        """Handle normal filtration mode (no lavage in progress)."""

        if self._should_activate_filtration():
            await self._activate_filtration_system()
        else:
            await self._deactivate_filtration_system()

    def _should_activate_filtration(self) -> bool:
        """Determine if filtration should be activated."""

        return (
            int(self.get_data("filtrationTemperature", 0)) == 1
            or int(self.get_data("filtrationSolaire", 0)) == 1
            or int(self.get_data("filtrationHivernage", 0)) == 1
            or int(self.get_data("filtrationSurpresseur", 0)) == 1
            or int(self.get_data("marcheForcee", 0)) == 1
        )

    async def _activate_filtration_system(self) -> None:
        """Activate filtration and associated devices."""

        await self.filtrationOn()

        # Activate treatment if needed
        if self._should_activate_treatment():
            await self._activate_treatment()

        # Handle surpresseur
        if int(self.get_data("filtrationSurpresseur", 0)) == 1:
            await asyncio.sleep(DEVICE_ACTIVATION_DELAY)
            await self.surpresseurOn()
        else:
            await self.surpresseurStop()

    def _should_activate_treatment(self) -> bool:
        """Determine if treatment should be activated."""

        return int(self.get_data("filtrationTemperature", 0)) == 1 or (
            int(self.get_data("filtrationHivernage", 0)) == 1
            and self.traitementHivernage is True
        )

    async def _activate_treatment(self) -> None:
        """Activate treatment devices with delay."""

        if self.traitement is not None or self.traitement_2 is not None:
            await asyncio.sleep(DEVICE_ACTIVATION_DELAY)

        if self.traitement is not None:
            await self.traitementOn()
        if self.traitement_2 is not None:
            await self.traitement_2_On()

    async def _deactivate_filtration_system(self) -> None:
        """Deactivate filtration and associated devices."""

        # Stop treatment first
        await self._deactivate_treatment()

        # Stop surpresseur
        if self.getStateSurpresseur() is True:
            await self.surpresseurStop()
            await asyncio.sleep(DEVICE_ACTIVATION_DELAY)

        # Stop filtration last
        await self.filtrationStop()

    async def _deactivate_treatment(self) -> None:
        """Deactivate treatment devices with delay."""

        if self.traitement is not None or self.traitement_2 is not None:
            if self.traitement is not None:
                if self.getStateTraitement() is True:
                    await self.traitementStop()
            if self.traitement_2 is not None:
                if self.getStateTraitement_2() is True:
                    await self.traitement_2_Stop()
            await asyncio.sleep(DEVICE_ACTIVATION_DELAY)

    async def _handle_lavage_stop_mode(self) -> None:
        """Handle lavage mode when devices need to be stopped."""

        if self.traitement is not None:
            await self.traitementStop()
        if self.traitement_2 is not None:
            await self.traitement_2_Stop()
        await self.surpresseurStop()
        await self.filtrationStop()

    async def _handle_lavage_filtration_mode(self) -> None:
        """Handle lavage mode when filtration is active."""

        if self.traitement is not None:
            await self.traitementStop()
        if self.traitement_2 is not None:
            await self.traitement_2_Stop()
        await self.surpresseurStop()
        await self.filtrationOn()

    async def _handle_stop_all(self) -> None:
        """Stop all devices (total stop mode)."""

        if self.traitement is not None:
            await self.traitementStop()
        if self.traitement_2 is not None:
            await self.traitement_2_Stop()
        await self.surpresseurStop()
        await self.filtrationStop()
