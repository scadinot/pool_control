"""Seasonal filtration logic for pool control."""

from datetime import datetime, timedelta
import logging
import time

_LOGGER = logging.getLogger(__name__)


class SaisonMixin:
    """Mixin providing seasonal filtration logic for pool control."""

    def calculateTimeFiltration(self, temperatureWater, flgTomorrow):
        """Calculate the filtration time."""

        temperatureCalcul = float(self.get_data("temperatureMaxi", 0))

        # Si pas de temperature maxi precedente on prend la temperature courante
        if temperatureCalcul == 0:
            temperatureCalcul = temperatureWater

        # Choix du type de calcul (suivant config)
        if self.methodeCalcul == 1:
            dureeHeures = self.calculateTimeFiltrationWithCurve(temperatureCalcul)
        else:
            dureeHeures = self.calculateTimeFiltrationWithTemperatureReducedByHalf(
                temperatureCalcul
            )

        filtrationSecondes, filtrationTime = self.processingTime(dureeHeures)

        # Mode normal

        # datePivot (suivant config)
        datePivot = self.datePivot  # 13:00

        # filtrationPivotSecondes = strtotime(datePivot)
        todayDate = datetime.today().date()
        combinedDatetime = datetime.strptime(
            str(todayDate) + " " + datePivot, "%Y-%m-%d %H:%M"
        )
        filtrationPivotSecondes = combinedDatetime.timestamp()

        # la plage doit-elle etre celle de demain ?
        if flgTomorrow is True:
            if filtrationPivotSecondes < time.time():
                _LOGGER.info("+1 day")
                filtrationPivotSecondes += timedelta(days=1).total_seconds()

        pausePivotSecondes = self.pausePivot * 60  # Temps de pause en secondes
        _LOGGER.debug(
            "duree pausePivot Config=%s",
            datetime.fromtimestamp(pausePivotSecondes).strftime("%H:%M"),
        )

        # si la somme de filtrationSecondes et pausePivotSecondes est superieure a 24h on reduit pausePivotSecondes
        if (filtrationSecondes + pausePivotSecondes) > (3600 * 24):
            _LOGGER.info(
                "duree pausePivot Ajustée=%s >> %s",
                datetime.fromtimestamp(pausePivotSecondes).strftime("%H:%M"),
                datetime.fromtimestamp((3600 * 24) - filtrationSecondes).strftime(
                    "%H:%M"
                ),
            )
            pausePivotSecondes = (3600 * 24) - filtrationSecondes

        filtrationSecondes += (
            pausePivotSecondes  # Ajoute le temps de pause au temps de filtration
        )

        # Repartition de la filtration suivant Config
        if self.distributionDatePivot == 1:
            # 1/2 <> 1/2
            _LOGGER.debug("distributionDatePivot= 1/2 <> 1/2")

            filtrationDebut = filtrationPivotSecondes - (filtrationSecondes / 2.0)
            filtrationFin = filtrationPivotSecondes + (filtrationSecondes / 2.0)

            filtrationPauseDebut = filtrationPivotSecondes - (pausePivotSecondes / 2.0)
            filtrationPauseFin = filtrationPivotSecondes + (pausePivotSecondes / 2.0)

        elif self.distributionDatePivot == 2:
            # 1/3 <> 2/3
            _LOGGER.debug("distributionDatePivot= 1/3 <> 2/3")

            filtrationDebut = filtrationPivotSecondes - (
                (filtrationSecondes / 3.0) * 1.0
            )
            filtrationFin = filtrationPivotSecondes + ((filtrationSecondes / 3.0) * 2.0)

            filtrationPauseDebut = filtrationPivotSecondes - (
                (pausePivotSecondes / 3.0) * 1.0
            )
            filtrationPauseFin = filtrationPivotSecondes + (
                (pausePivotSecondes / 3.0) * 2.0
            )

        elif self.distributionDatePivot == 3:
            # 2/3 <> 1/3
            _LOGGER.debug("distributionDatePivot= 2/3 <> 1/3")

            filtrationDebut = filtrationPivotSecondes - (
                (filtrationSecondes / 3.0) * 2.0
            )
            filtrationFin = filtrationPivotSecondes + ((filtrationSecondes / 3.0) * 1.0)

            filtrationPauseDebut = filtrationPivotSecondes - (
                (pausePivotSecondes / 3.0) * 2.0
            )
            filtrationPauseFin = filtrationPivotSecondes + (
                (pausePivotSecondes / 3.0) * 1.0
            )

        elif self.distributionDatePivot == 4:
            # 1/1 <>
            _LOGGER.debug("distributionDatePivot= 1/1 <>")

            filtrationDebut = filtrationPivotSecondes - filtrationSecondes
            filtrationFin = filtrationPivotSecondes

            filtrationPauseDebut = filtrationPivotSecondes - (pausePivotSecondes / 2.0)
            filtrationPauseFin = filtrationPivotSecondes + (pausePivotSecondes / 2.0)

        elif self.distributionDatePivot == 5:
            # <> 1/1
            _LOGGER.debug("distributionDatePivot= <> 1/1")

            filtrationDebut = filtrationPivotSecondes
            filtrationFin = filtrationPivotSecondes + filtrationSecondes

            filtrationPauseDebut = filtrationPivotSecondes - (pausePivotSecondes / 2.0)
            filtrationPauseFin = filtrationPivotSecondes + (pausePivotSecondes / 2.0)

        # Memorise les resultats du calcul
        if self.filtrationTimeStatus:
            self.filtrationTimeStatus.set_status(filtrationTime)

        if filtrationPauseDebut != filtrationPauseFin:
            display = datetime.fromtimestamp(filtrationDebut).strftime("%H:%M")
            display += "-"
            display += datetime.fromtimestamp(filtrationPauseDebut).strftime("%H:%M")
            display += " "
            display += datetime.fromtimestamp(filtrationPauseFin).strftime("%H:%M")
            display += "-"
            display += datetime.fromtimestamp(filtrationFin).strftime("%H:%M")
            display += " : "
            display += str(temperatureCalcul)
            display += "°C"
            if self.filtrationScheduleStatus:
                self.filtrationScheduleStatus.set_status(display)
        else:
            display = datetime.fromtimestamp(filtrationDebut).strftime("%H:%M")
            display += "-"
            display += datetime.fromtimestamp(filtrationFin).strftime("%H:%M")
            display += " : "
            display += str(temperatureCalcul)
            display += "°C"
            if self.filtrationScheduleStatus:
                self.filtrationScheduleStatus.set_status(display)

        self.set_data("filtrationDebut", int(filtrationDebut))
        self.set_data("filtrationFin", int(filtrationFin))
        self.set_data("filtrationPauseDebut", int(filtrationPauseDebut))
        self.set_data("filtrationPauseFin", int(filtrationPauseFin))

        self.set_data("calculateStatus", 1)  # 1 >> calcul effectué

        if flgTomorrow is True:
            self.set_data("temperatureMaxi", 0)  # reset temperature maxi

        _LOGGER.info("temperatureCalcul=%s", temperatureCalcul)
        _LOGGER.info("filtrationTime=%s", filtrationTime)

        _LOGGER.info(
            "filtrationDebut=%s",
            datetime.fromtimestamp(filtrationDebut).strftime("%H:%M %d-%m-%Y"),
        )

        if filtrationPauseDebut != filtrationPauseFin:
            _LOGGER.info(
                "filtrationPauseDebut=%s",
                datetime.fromtimestamp(filtrationPauseDebut).strftime("%H:%M %d-%m-%Y"),
            )
            _LOGGER.info(
                "filtrationPauseFin=%s",
                datetime.fromtimestamp(filtrationPauseFin).strftime("%H:%M %d-%m-%Y"),
            )

        _LOGGER.info(
            "filtrationFin=%s",
            datetime.fromtimestamp(filtrationFin).strftime("%H:%M %d-%m-%Y"),
        )

    async def calculateStatusFiltration(self, temperatureWater):
        """Calculate the filtration state in Saison mode."""

        filtrationTemperature = 0
        filtrationDebut = self.get_data("filtrationDebut", 0)
        filtrationPauseDebut = self.get_data("filtrationPauseDebut", 0)
        filtrationPauseFin = self.get_data("filtrationPauseFin", 0)
        filtrationFin = self.get_data("filtrationFin", 0)

        timeNow = time.time()
        _LOGGER.info(
            "calculateStatusFiltration: timeNow=%s",
            datetime.fromtimestamp(timeNow).strftime("%H:%M %d-%m-%Y"),
        )
        _LOGGER.info(
            "calculateStatusFiltration: filtrationDebut=%s",
            datetime.fromtimestamp(filtrationDebut).strftime("%H:%M %d-%m-%Y"),
        )
        _LOGGER.info(
            "calculateStatusFiltration: filtrationFin=%s",
            datetime.fromtimestamp(filtrationFin).strftime("%H:%M %d-%m-%Y"),
        )

        if filtrationDebut == 0 or filtrationFin == 0:
            # Le calcul n'a jamais ete lancé, on le lance maintenant
            self.calculateTimeFiltration(temperatureWater, False)

            # Verifie si la plage calculée est passée
            filtrationFin = self.get_data("filtrationFin", 0)
            timeNow = time.time()

            if timeNow > filtrationFin:
                # On est apres la plage de filtration, relancer le calcul pour la plage de demain
                self.calculateTimeFiltration(temperatureWater, True)

        else:
            if filtrationPauseDebut != filtrationPauseFin:
                # Pause de filtration active

                # Premier segment
                if timeNow >= filtrationDebut and timeNow <= filtrationPauseDebut:
                    if timeNow >= filtrationDebut + (60 * 5):
                        self.hass.states.async_set(
                            "input_number.temperatureDisplay", temperatureWater
                        )

                    # Active la filtration
                    filtrationTemperature = 1

                # Deuxieme segment
                if timeNow >= filtrationPauseFin and timeNow <= filtrationFin:
                    if self.sondeLocalTechnique is True:
                        if timeNow >= filtrationPauseFin + (
                            60 * self.sondeLocalTechniquePause
                        ):
                            self.hass.states.async_set(
                                "input_number.temperatureDisplay", temperatureWater
                            )

                            # Determine la temperature maxi pour le prochain calcul
                            temperatureMaxi = float(self.get_data("temperatureMaxi", 0))

                            if temperatureWater > temperatureMaxi:
                                self.set_data("temperatureMaxi", temperatureWater)
                                _LOGGER.debug("temperatureMaxi: %s", temperatureMaxi)
                                _LOGGER.debug("temperatureWater: %s", temperatureWater)
                                _LOGGER.debug(
                                    "(temperatureWater > temperatureMaxi) >> temperatureMaxi=: %s",
                                    temperatureWater,
                                )

                    else:
                        # Determine la temperature maxi pour le prochain calcul
                        temperatureMaxi = float(self.get_data("temperatureMaxi", 0))

                        if temperatureWater > temperatureMaxi:
                            self.set_data("temperatureMaxi", temperatureWater)
                            _LOGGER.debug("temperatureMaxi: %s", temperatureMaxi)
                            _LOGGER.debug("temperatureWater: %s", temperatureWater)
                            _LOGGER.debug(
                                "(temperatureWater > temperatureMaxi) >> temperatureMaxi=: %s",
                                temperatureWater,
                            )

                    # Active la filtration
                    filtrationTemperature = 1

            elif timeNow >= filtrationDebut and timeNow <= filtrationFin:
                if self.sondeLocalTechnique is True:
                    if timeNow >= filtrationDebut + (
                        60 * self.sondeLocalTechniquePause
                    ):
                        self.hass.states.async_set(
                            "input_number.temperatureDisplay", temperatureWater
                        )

                        # Determine la temperature maxi pour le prochain calcul
                        temperatureMaxi = float(self.get_data("temperatureMaxi", 0))

                        if temperatureWater > temperatureMaxi:
                            self.set_data("temperatureMaxi", temperatureWater)

                            _LOGGER.debug("temperatureMaxi: %s", temperatureMaxi)
                            _LOGGER.debug("temperatureWater: %s", temperatureWater)
                            _LOGGER.debug(
                                "(temperatureWater > temperatureMaxi) >> temperatureMaxi=: %s",
                                temperatureWater,
                            )

                else:
                    # Determine la temperature maxi pour le prochain calcul
                    temperatureMaxi = float(self.get_data("temperatureMaxi"))

                    if temperatureWater > temperatureMaxi:
                        self.set_data("temperatureMaxi", temperatureWater)

                        _LOGGER.debug("temperatureMaxi: %s", temperatureMaxi)
                        _LOGGER.debug("temperatureWater: %s", temperatureWater)
                        _LOGGER.debug(
                            "(temperatureWater > temperatureMaxi) >> temperatureMaxi=: %s",
                            temperatureWater,
                        )

                # Active la filtration
                filtrationTemperature = 1

            if filtrationTemperature == 1:
                if self.disableMarcheForcee is True:
                    if int(self.get_data("marcheForcee", 0)) == 1:
                        self.set_data("marcheForcee", 0)

                if int(self.get_data("calculateStatus", 0)) != 0:
                    self.set_data("calculateStatus", 0)

            calculateStatus = int(self.get_data("calculateStatus", 0))

            if timeNow > filtrationFin and calculateStatus == 0:
                # On est apres la plage de filtration, relancer le calcul pour la plage de demain
                self.calculateTimeFiltration(temperatureWater, True)
                self.hass.states.async_set(
                    "input_number.temperatureDisplay", temperatureWater
                )

        if int(self.get_data("filtrationTemperature", 0)) != filtrationTemperature:
            self.set_data("filtrationTemperature", filtrationTemperature)

        if int(self.get_data("filtrationHivernage", 0)) != 0:
            self.set_data("filtrationHivernage", 0)
