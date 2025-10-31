"""Hivernage (wintering) logic for pool control integration."""

from datetime import datetime, timedelta
import logging
import time

_LOGGER = logging.getLogger(__name__)


class HivernageMixin:
    """Mixin providing hivernage (wintering) logic for pool control integration."""

    def getHivernage(self):
        """Determine if the pool is in hivernage mode."""

        if int(self.get_data("hivernageWidgetStatus", 0)) == 1:
            flgHivernage = True
        else:
            flgHivernage = False

        return flgHivernage

    def getStatusHivernage(self, status):
        """Determine the status of the hivernage mode."""

        if int(self.get_data("hivernageWidgetStatus", 0)) == 1:
            status = status + " " + "Hivernage"
        else:
            status = status + " " + "Saison"

        return status

    def calculateTimeFiltrationHivernage(self, temperatureWater, flgTomorrow):
        """Calculate the filtration period in hivernage mode."""

        temperatureCalcul = float(self.get_data("temperatureMaxi", 0))

        # Si pas de temperature maxi precedente on prend la temperature courante
        if temperatureCalcul == 0:
            temperatureCalcul = temperatureWater

        dureeHeures = self.calculateTimeFiltrationWithTemperatureHivernage(
            temperatureCalcul
        )

        filtrationSecondes, filtrationTime = self.processingTime(dureeHeures)

        # Choix de l'heure de filtration (suivant config)
        if self.choixHeureFiltrationHivernage == 1:
            datePivot = self.getLeverSoleil()
        else:
            datePivot = self.datePivotHivernage

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

        # Repartition de la filtration suivant Config
        if self.distributionDatePivotHivernage == 1:
            # 1/2 <> 1/2
            _LOGGER.debug("distributionDatePivotHivernage= 1/2 <> 1/2")

            filtrationDebut = filtrationPivotSecondes - (filtrationSecondes / 2.0)
            filtrationFin = filtrationPivotSecondes + (filtrationSecondes / 2.0)

        elif self.distributionDatePivotHivernage == 2:
            # 1/3 <> 2/3
            _LOGGER.debug("distributionDatePivotHivernage= 1/3 <> 2/3")

            filtrationDebut = filtrationPivotSecondes - (
                (filtrationSecondes / 3.0) * 1.0
            )
            filtrationFin = filtrationPivotSecondes + ((filtrationSecondes / 3.0) * 2.0)

        elif self.distributionDatePivotHivernage == 3:
            # 2/3 <> 1/3
            _LOGGER.debug("distributionDatePivotHivernage= 2/3 <> 1/3")

            filtrationDebut = filtrationPivotSecondes - (
                (filtrationSecondes / 3.0) * 2.0
            )
            filtrationFin = filtrationPivotSecondes + ((filtrationSecondes / 3.0) * 1.0)

        elif self.distributionDatePivotHivernage == 4:
            # 1/1 <>
            _LOGGER.debug("distributionDatePivotHivernage= 1/1 <>")

            filtrationDebut = filtrationPivotSecondes - filtrationSecondes
            filtrationFin = filtrationPivotSecondes

        elif self.distributionDatePivotHivernage == 5:
            # <> 1/1
            _LOGGER.debug("distributionDatePivotHivernage= <> 1/1")

            filtrationDebut = filtrationPivotSecondes
            filtrationFin = filtrationPivotSecondes + filtrationSecondes

        # Memorise les resultats du calcul
        if self.filtrationTimeStatus:
            self.filtrationTimeStatus.set_status(filtrationTime)

        display = "* "
        display += datetime.fromtimestamp(filtrationDebut).strftime("%H:%M")
        display += "-"
        display += datetime.fromtimestamp(filtrationFin).strftime("%H:%M")
        display += " : "
        display += str(temperatureCalcul)
        display += "°C"
        if self.filtrationScheduleStatus:
            self.filtrationScheduleStatus.set_status(display)

        self.set_data("filtrationDebut", int(filtrationDebut))
        self.set_data("filtrationFin", int(filtrationFin))

        self.set_data("calculateStatus", 1)  # 1 >> calcul effectué

        if flgTomorrow is True:
            self.set_data("temperatureMaxi", 0)  # reset temperature maxi

        _LOGGER.info("temperatureCalcul=%s", temperatureCalcul)
        _LOGGER.info("filtrationTime=%s", filtrationTime)

        _LOGGER.info(
            "filtrationDebut=%s",
            datetime.fromtimestamp(filtrationDebut).strftime("%H:%M %d-%m-%Y"),
        )
        _LOGGER.info(
            "filtrationFin=%s",
            datetime.fromtimestamp(filtrationFin).strftime("%H:%M %d-%m-%Y"),
        )

    async def calculateStatusFiltrationHivernage(
        self, temperatureWater, temperatureOutdoor
    ):
        """Calculate the filtration state in hivernage mode."""

        filtrationHivernage = 0

        filtrationDebut = self.get_data("filtrationDebut", 0)
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
            self.calculateTimeFiltrationHivernage(temperatureWater, False)

            # Verifie si la plage calculée est passée
            filtrationFin = self.get_data("filtrationFin", 0)
            timeNow = time.time()

            if timeNow > filtrationFin:
                # On est apres la plage de filtration, relancer le calcul pour la plage de demain
                self.calculateTimeFiltrationHivernage(temperatureWater, True)

        else:
            if timeNow >= filtrationDebut and timeNow <= filtrationFin:
                if self.sondeLocalTechnique is True:
                    if timeNow >= filtrationDebut + (
                        60 * self.sondeLocalTechniquePause
                    ):
                        self.updateTemperatureDisplay(temperatureWater)

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
                filtrationHivernage = 1

            if filtrationHivernage == 1:
                if self.disableMarcheForcee is True:
                    if int(self.get_data("marcheForcee", 0)) == 1:
                        self.set_data("marcheForcee", 0)

                if int(self.get_data("calculateStatus", 0)) != 0:
                    self.set_data("calculateStatus", 0)

            calculateStatus = int(self.get_data("calculateStatus", 0))

            if timeNow > filtrationFin and calculateStatus == 0:
                # On est apres la plage de filtration, relancer le calcul pour la plage de demain
                self.calculateTimeFiltrationHivernage(temperatureWater, True)
                self.updateTemperatureDisplay(temperatureWater)

        # Recupere l'etat precedent de filtrationHivernageSecurite
        filtrationHivernageSecurite = int(
            self.get_data("filtrationHivernageSecurite", 0)
        )

        if filtrationHivernageSecurite != 0:
            # La filtration etait deja active on verifie si la temperature est remontee suffisament (Hysteresis...)
            if temperatureOutdoor > (
                self.temperatureSecurite + self.temperatureHysteresis
            ):
                _LOGGER.debug(
                    "Arret securité gel sur temperature exterieure > %s",
                    self.temperatureSecurite + self.temperatureHysteresis,
                )

                filtrationHivernageSecurite = 0

        elif temperatureOutdoor < self.temperatureSecurite:
            _LOGGER.debug(
                "Securité gel sur temperature exterieure < %s", self.temperatureSecurite
            )

            filtrationHivernageSecurite = 1

        self.set_data("filtrationHivernageSecurite", filtrationHivernageSecurite)

        # Securité gel sur temperature exterieure < temperatureSecurite
        if filtrationHivernageSecurite != 0:
            filtrationHivernage = 1

        # 5mn toutes les 3H
        if self.filtration5mn3h:
            currentTime = datetime.now().strftime("%H%M")

            if (
                "0200" <= currentTime <= "0205"
                or "0500" <= currentTime <= "0505"
                or "0800" <= currentTime <= "0805"
                or "1100" <= currentTime <= "1105"
                or "1400" <= currentTime <= "1405"
                or "1700" <= currentTime <= "1705"
                or "2000" <= currentTime <= "2005"
                or "2300" <= currentTime <= "2305"
            ):
                filtrationHivernage = 1

        if int(self.get_data("filtrationHivernage", 0)) != filtrationHivernage:
            self.set_data("filtrationHivernage", filtrationHivernage)

        if int(self.get_data("filtrationTemperature", 0)) != 0:
            self.set_data("filtrationTemperature", 0)
