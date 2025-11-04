"""Lavage mixin for pool control."""

from datetime import datetime
import time
from typing import Optional


class LavageMixin:
    """Mixin class providing lavage (filter cleaning) logic for pool control."""

    async def executeFiltreSableLavageOn(self) -> None:
        """Lance le lavage du filtre à sable."""

        if self.get_data("filtrationSurpresseur", 0) == 0:
            lavageState = int(self.get_data("filtrationLavageEtat", 0))

            if lavageState == 0:
                # Arrêt, mettre la vanne sur la position lavage
                self.set_data("filtrationLavageEtat", 1)
                if self.filtreSableLavageStatus:
                    self.filtreSableLavageStatus.set_status("Arrêt, position lavage")
                self.set_data("filtrationLavage", 1)
                await self.activatingDevices()

                await self.startSecondCron()

            elif lavageState == 1:
                if self.rincageDuree == 0:
                    # Si le temps de rinçage est == 0 on passe directement à la fin
                    self.set_data("filtrationLavageEtat", 4)  # Rinçage en cours...
                else:
                    self.set_data("filtrationLavageEtat", 2)  # Lavage en cours...

                timeFin = time.time() + (self.lavageDuree * 60)
                self.set_data("filtrationTempsRestant", int(timeFin))

                timeRestant = timeFin - int(time.time())
                display = "Lavage"
                display += " : "
                display += datetime.fromtimestamp(timeRestant).strftime("%M:%S")
                if self.filtreSableLavageStatus:
                    self.filtreSableLavageStatus.set_status(display)
                self.set_data("filtrationLavage", 2)
                await self.activatingDevices()

            elif lavageState == 2:
                # Arrêt, mettre la vanne sur la position rinçage
                self.set_data("filtrationLavageEtat", 3)
                if self.filtreSableLavageStatus:
                    self.filtreSableLavageStatus.set_status("Arrêt, position rinçage")
                self.set_data("filtrationLavage", 1)
                await self.activatingDevices()

            elif lavageState == 3:
                # Rinçage en cours...
                self.set_data("filtrationLavageEtat", 4)
                timeFin = time.time() + (self.rincageDuree * 60)
                self.set_data("filtrationTempsRestant", int(timeFin))

                timeRestant = timeFin - time.time()
                display = "Rinçage"
                display += " : "
                display += datetime.fromtimestamp(timeRestant).strftime("%M:%S")
                if self.filtreSableLavageStatus:
                    self.filtreSableLavageStatus.set_status(display)
                self.set_data("filtrationLavage", 2)
                await self.activatingDevices()

            elif lavageState == 4:
                # Arrêt, mettre la vanne sur la position filtration
                self.set_data("filtrationLavageEtat", 5)
                if self.filtreSableLavageStatus:
                    self.filtreSableLavageStatus.set_status(
                        "Arrêt, position filtration"
                    )
                self.set_data("filtrationLavage", 1)
                await self.activatingDevices()

            elif lavageState == 5:
                # Arrêté
                self.set_data("filtrationLavageEtat", 0)
                if self.filtreSableLavageStatus:
                    self.filtreSableLavageStatus.set_status("Arrêté")
                self.set_data("filtrationLavage", 0)
                await self.activatingDevices()

                await self.stopSecondCron()
