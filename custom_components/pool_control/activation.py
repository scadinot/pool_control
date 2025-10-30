"""Activation logic for pool control devices."""

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


class ActivationMixin:
    """Mixin for activation logic of pool control devices."""

    async def activatingDevices(self):  # noqa: C901
        """Active les appareils de filtration et de traitement."""

        _LOGGER.debug("activatingDevices() begin")

        # _LOGGER.info(f"FiltrationLavagek={int(self.get_data('FiltrationLavage', 0))}")
        # _LOGGER.info(f"FiltrationLavageEtat={int(self.get_data('FiltrationLavageEtat', 0))}")
        # _LOGGER.info(f"FiltrationTemperature={int(self.get_data('FiltrationTemperature', 0))}")
        # _LOGGER.info(f"FiltrationSolaire={int(self.get_data('FiltrationSolaire', 0))}")
        # _LOGGER.info(f"FiltrationHivernage={int(self.get_data('FiltrationHivernage', 0))}")
        # _LOGGER.info(f"FiltrationSurpresseur={int(self.get_data('FiltrationSurpresseur', 0))}")
        # _LOGGER.info(f"ArretTotal={int(self.get_data('ArretTotal', 0))}")
        # _LOGGER.info(f"MarcheForcee={int(self.get_data('FiltrationLavage', 0))}")

        if int(self.get_data("arretTotal", 0)) == 0:
            if int(self.get_data("marcheForcee", 0)) == 1:
                # Marche forcée, filtration desactivée
                status = "Actif"
                status = self.getStatusHivernage(status)
                if self.asservissementStatus:
                    self.asservissementStatus.set_status(status)
            else:
                # Mode Auto, filtration pendant les plages programmées
                status = "Auto"
                status = self.getStatusHivernage(status)
                if self.asservissementStatus:
                    self.asservissementStatus.set_status(status)
        else:
            # Arret total, prioritaire > (tout est stoppé)
            status = "Inactif"
            status = self.getStatusHivernage(status)
            if self.asservissementStatus:
                self.asservissementStatus.set_status(status)

        if int(self.get_data("arretTotal", 0)) == 0:
            if int(self.get_data("filtrationLavage", 0)) == 0:
                if (
                    int(self.get_data("filtrationTemperature", 0)) == 1
                    or int(self.get_data("filtrationSolaire", 0)) == 1
                    or int(self.get_data("filtrationHivernage", 0)) == 1
                    or int(self.get_data("filtrationSurpresseur", 0)) == 1
                    or int(self.get_data("marcheForcee", 0)) == 1
                ):
                    await self.filtrationOn()

                    if int(self.get_data("filtrationTemperature", 0)) == 1 or (
                        int(self.get_data("filtrationHivernage", 0)) == 1
                        and self.traitementHivernage is True
                    ):
                        if self.traitement is not None or self.traitement_2 is not None:
                            await asyncio.sleep(2)
                        if self.traitement is not None:
                            await self.traitementOn()
                        if self.traitement_2 is not None:
                            await self.traitement_2_On()

                    if int(self.get_data("filtrationSurpresseur", 0)) == 1:
                        await asyncio.sleep(2)
                        await self.surpresseurOn()
                    else:
                        await self.surpresseurStop()
                else:
                    if self.traitement is not None or self.traitement_2 is not None:
                        if self.traitement is not None:
                            if self.getStateTraitement() is True:
                                await self.traitementStop()
                        if self.traitement_2 is not None:
                            if self.getStateTraitement_2() is True:
                                await self.traitement_2_Stop()
                        await asyncio.sleep(2)

                    if self.getStateSurpresseur() is True:
                        await self.surpresseurStop()
                        await asyncio.sleep(2)

                    await self.filtrationStop()

            if int(self.get_data("filtrationLavage", 0)) == 1:
                if self.traitement is not None:
                    await self.traitementStop()
                if self.traitement_2 is not None:
                    await self.traitement_2_Stop()
                await self.surpresseurStop()
                await self.filtrationStop()

            if int(self.get_data("filtrationLavage", 0)) == 2:
                if self.traitement is not None:
                    await self.traitementStop()
                if self.traitement_2 is not None:
                    await self.traitement_2_Stop()
                await self.surpresseurStop()
                await self.filtrationOn()

        else:
            if self.traitement is not None:
                await self.traitementStop()
            if self.traitement_2 is not None:
                await self.traitement_2_Stop()
            await self.surpresseurStop()
            await self.filtrationStop()

        _LOGGER.debug("activatingDevices() end")
