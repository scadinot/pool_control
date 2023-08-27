import asyncio
import logging
import time
from datetime import datetime, timedelta

from homeassistant import config_entries
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import _LOGGER, HomeAssistant
from homeassistant.helpers.event import (
    async_track_state_change,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

# DEFAULT_NAME = "Pool Control"
DOMAIN = "pool_control"
STORAGE_VERSION = 1
STORAGE_KEY = "pool_control_data"


class PoolController:
    ###############################################################################################################################################################################

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialisation classe PoolControler"""

        # configuration.yaml
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data = {}
        self.initialized = False

        self.temperatureWater = config["temperatureWater"]
        self.temperatureOutdoor = config["temperatureOutdoor"]
        self.leverSoleil = config["leverSoleil"]

        self.buttonReset = config["buttonReset"]
        self.buttonResetFirstCall = True

        self.buttonSurpresseur = config["buttonSurpresseur"]
        self.buttonSurpresseurFirstCall = True

        self.buttonLavage = config["buttonLavage"]
        self.buttonLavageFirstCall = True

        self.buttonStop = config["buttonStop"]
        self.buttonStopFirstCall = True

        self.buttonActif = config["buttonActif"]
        self.buttonActifFirstCall = True
        self.buttonAuto = config["buttonAuto"]
        self.buttonAutoFirstCall = True
        self.buttonInactif = config["buttonInactif"]
        self.buttonInactifFirstCall = True

        self.buttonSaison = config["buttonSaison"]
        self.buttonSaisonFirstCall = True
        self.buttonHivernage = config["buttonHivernage"]
        self.buttonHivernageFirstCall = True

        self.filtration = config["filtration"]
        self.traitement = config["traitement"]
        self.surpresseur = config["surpresseur"]

        self.surpresseurDuree = config.get("surpresseurDuree", 10)

        self.disableMarcheForcee = config.get("disableMarcheForcee", False)
        self.methodeCalcul = config.get("methodeCalcul", 1)
        self.datePivot = config.get("datePivot", "13:00")
        self.pausePivot = config.get("pausePivot", 0)
        self.distributionDatePivot = config.get("distributionDatePivot", 1)
        self.coefficientAjustement = config.get("coefficientAjustement", 1.0)
        self.sondeLocalTechnique = config.get("sondeLocalTechnique", False)
        self.sondeLocalTechniquePause = config.get("sondeLocalTechniquePause", 0)

        self.traitementHivernage = config.get("traitementHivernage", False)
        self.tempsDeFiltrationMinimum = config.get("tempsDeFiltrationMinimum", 3)
        self.choixHeureFiltrationHivernage = config.get(
            "choixHeureFiltrationHivernage", 1
        )
        self.datePivotHivernage = config.get("datePivotHivernage", "06:00")
        self.temperatureSecurite = config.get("temperatureSecurite", -1)
        self.temperatureHysteresis = config.get("temperatureHysteresis", 0.5)
        self.filtration5mn3h = config.get("filtration5mn3h", False)

        self.lavageDuree = config.get("lavageDuree", 2)
        self.rincageDuree = config.get("rincageDuree", 2)

        self.secondCronCancel = None

        # Propriétés de l'objet
        self.filtrationRefreshCounter = 0

        return None

    ###############################################################################################################################################################################

    async def startSecondCron(self):
        """Lance le cron '5 secondes'."""

        if self.secondCronCancel is not None:
            self.secondCronCancel()

        # Call 'pull' method every 5 secondes
        self.secondCronCancel = async_track_time_interval(
            self.hass, self.pull, timedelta(seconds=5)
        )

        _LOGGER.info("Second cron job start")

        return

    async def stopSecondCron(self):
        """Arrete le cron '5 secondes'."""

        if self.secondCronCancel is not None:
            self.secondCronCancel()
            self.secondCronCancel = None

            _LOGGER.info("Second cron job stop")

        return

    async def pull(self, now=None):
        """Boucle secondaire appellée toutes les 5 secondes"""

        _LOGGER.debug("pull() begin")

        if int(self.get_data("filtrationSurpresseur", 0)) == 1:
            timeFin = self.get_data("filtrationTempsRestant", 0)
            timeRestant = timeFin - time.time()

            if timeRestant > 0:
                display = "Actif"
                display += " : "
                display += datetime.fromtimestamp(timeRestant).strftime("%M:%S")
                self.hass.states.async_set("input_text.surpresseurStatus", display)
            else:
                await self.executePoolStop()

        if int(self.get_data("filtrationLavageEtat", 0)) == 2:
            timeFin = self.get_data("filtrationTempsRestant", 0)
            timeRestant = timeFin - time.time()

            if timeRestant > 0:
                display = "Lavage"
                display += " : "
                display += datetime.fromtimestamp(timeRestant).strftime("%M:%S")
                self.hass.states.async_set(
                    "input_text.filtreSableLavageStatus", display
                )
            else:
                await self.executeFiltreSableLavageOn()

        if int(self.get_data("filtrationLavageEtat", 0)) == 4:
            timeFin = self.get_data("filtrationTempsRestant", 0)
            timeRestant = timeFin - time.time()

            if timeRestant > 0:
                display = "Rinçage"
                display += " : "
                display += datetime.fromtimestamp(timeRestant).strftime("%M:%S")
                self.hass.states.async_set(
                    "input_text.filtreSableLavageStatus", display
                )
            else:
                await self.executeFiltreSableLavageOn()

        _LOGGER.debug("pull() end")
        return

    ###############################################################################################################################################################################

    async def startFirstCron(self):
        """Lance le cron '1 minute'."""

        # Call 'cron' method every 1 minute
        async_track_time_interval(self.hass, self.cron, timedelta(minutes=1))

        _LOGGER.info("Second cron job start")

        return

    async def cron(self, now=None):
        """Boucle principale appellée toutes les 1 minute"""

        _LOGGER.debug("cron() begin")

        ###########################################################################################

        temperatureWater = self.getTemperatureWater()
        temperatureOutdoor = self.getTemperatureOutdoor()
        # leverSoleil = self.getLeverSoleil()

        ###########################################################################################

        if self.filtrationRefreshCounter >= 5:
            # Refresh appellé toutes les 5 minutes

            _LOGGER.info(
                f"Time = {datetime.fromtimestamp(time.time()).strftime('%H:%M %d-%m-%Y')}"
            )

            # _LOGGER.info(f"temperatureWater={temperatureWater}")
            # _LOGGER.info(f"temperatureOutdoor={temperatureOutdoor}")
            # _LOGGER.info(f"leverSoleil={leverSoleil}")

            await self.refreshFiltration()
            await self.refreshSurpresseur()
            await self.refreshTraitement()
            # await self.refreshChauffage()

            self.filtrationRefreshCounter = 0
        else:
            self.filtrationRefreshCounter += 1

        ###########################################################################################

        if self.getHivernage() == True:
            await self.calculateStatusFiltrationHivernage(
                temperatureWater, temperatureOutdoor
            )
        else:
            await self.calculateStatusFiltration(temperatureWater)

        ###########################################################################################

        await self.activatingDevices()

        ###########################################################################################

        _LOGGER.debug("cron() end")

        return

    ###############################################################################################################################################################################

    async def activatingDevices(self):
        """Activation des Devices"""

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
                self.hass.states.async_set("input_text.asservissementStatus", status)
            else:
                # Mode Auto, filtration pendant les plages programmées
                status = "Auto"
                status = self.getStatusHivernage(status)
                self.hass.states.async_set("input_text.asservissementStatus", status)
        else:
            # Arret total, prioritaire > (tout est stoppé)
            status = "Inactif"
            status = self.getStatusHivernage(status)
            self.hass.states.async_set("input_text.asservissementStatus", status)

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
                        and self.traitementHivernage == True
                    ):
                        await asyncio.sleep(2)
                        await self.traitementOn()

                    if int(self.get_data("filtrationSurpresseur", 0)) == 1:
                        await asyncio.sleep(2)
                        await self.surpresseurOn()
                    else:
                        await self.surpresseurStop()
                else:
                    if self.getStateTraitement() == True:
                        await self.traitementStop()
                        await asyncio.sleep(2)

                    if self.getStateSurpresseur() == True:
                        await self.surpresseurStop()
                        await asyncio.sleep(2)

                    await self.filtrationStop()

            if int(self.get_data("filtrationLavage", 0)) == 1:
                await self.traitementStop()
                await self.surpresseurStop()
                await self.filtrationStop()

            if int(self.get_data("filtrationLavage", 0)) == 2:
                await self.traitementStop()
                await self.surpresseurStop()
                await self.filtrationOn()

        else:
            await self.traitementStop()
            await self.surpresseurStop()
            await self.filtrationStop()

        _LOGGER.debug("activatingDevices() end")

        return

    def processingTime(self, dureeHeures):
        # Arrondi en minutes
        dureeHeures = int(dureeHeures * 60) / 60

        # La durée ne peut pas être supérieure à 24 H
        dureeHeures = min(dureeHeures, 24.00)

        # Conversion en secondes pour les calculs
        filtrationSecondes = dureeHeures * 3600.0

        # Conversion en hh:mm pour l'affichage
        hh = int(dureeHeures)
        mm = int((dureeHeures * 60) - (hh * 60))

        filtrationTime = f"{hh:02d}:{mm:02d}"

        return filtrationSecondes, filtrationTime

    ###############################################################################################################################################################################

    def calculateTimeFiltrationWithCurve(self, temperatureWater):
        # Pour assurer un temps minimum de filtration, la température de calcul est forcée à 10°C
        temperature = max(temperatureWater, 10.0)

        # Coefficients de l'équation
        a = 0.00335
        b = -0.14953
        c = 2.43489
        d = -10.72859

        # Coefficient d'ajustement de la courbe (suivant config)
        coeff = self.coefficientAjustement

        a *= coeff
        b *= coeff
        c *= coeff
        d *= coeff

        dureeHeures = (
            (a * pow(temperature, 3))
            + (b * pow(temperature, 2))
            + (c * temperature)
            + d
        )

        return dureeHeures

    def calculateTimeFiltrationWithTemperatureReducedByHalf(self, temperatureWater):
        # Calcul simplifié
        dureeHeures = temperatureWater / 2.0

        # Coefficient d'ajustement (suivant config)
        dureeHeures *= self.coefficientAjustement

        return dureeHeures

    def calculateTimeFiltration(self, temperatureWater, flgTomorrow):
        temperatureCalcul = float(self.get_data("temperatureMaxi", 0))

        # Si pas de temperature maxi precedente on prend la temperature courante
        if temperatureCalcul == 0 or temperatureCalcul == 0:
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
        if flgTomorrow == True:
            if filtrationPivotSecondes < time.time():
                _LOGGER.info(f"+1 day")
                filtrationPivotSecondes += timedelta(days=1).total_seconds()

        pausePivotSecondes = self.pausePivot * 60  # Temps de pause en secondes
        _LOGGER.debug(
            f"duree pausePivot Config={datetime.fromtimestamp(pausePivotSecondes).strftime('%H:%M')}"
        )

        # si la somme de filtrationSecondes et pausePivotSecondes est superieure a 24h on reduit pausePivotSecondes
        if (filtrationSecondes + pausePivotSecondes) > (3600 * 24):
            _LOGGER.info(
                f"duree pausePivot Ajustée={datetime.fromtimestamp(pausePivotSecondes).strftime('%H:%M')} >> {datetime.fromtimestamp((3600 * 24) - filtrationSecondes).strftime('%H:%M')}"
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

            filtrationDebut = filtrationPivotSecondes - (filtrationSecondes / 3.0)
            filtrationFin = filtrationPivotSecondes + ((filtrationSecondes / 3.0) * 2.0)

            filtrationPauseDebut = filtrationPivotSecondes - (pausePivotSecondes / 3.0)
            filtrationPauseFin = filtrationPivotSecondes + (
                (pausePivotSecondes / 3.0) * 2.0
            )

        # Memorise les resultats du calcul
        self.hass.states.async_set("input_text.filtrationTime", filtrationTime)

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
            self.hass.states.async_set("input_text.filtrationSchedule", display)
        else:
            display = datetime.fromtimestamp(filtrationDebut).strftime("%H:%M")
            display += "-"
            display += datetime.fromtimestamp(filtrationFin).strftime("%H:%M")
            display += " : "
            display += str(temperatureCalcul)
            display += "°C"
            self.hass.states.async_set("input_text.filtrationSchedule", display)

        self.set_data("filtrationDebut", int(filtrationDebut))
        self.set_data("filtrationFin", int(filtrationFin))
        self.set_data("filtrationPauseDebut", int(filtrationPauseDebut))
        self.set_data("filtrationPauseFin", int(filtrationPauseFin))

        self.set_data("calculateStatus", 1)  # 1 >> calcul effectué

        if flgTomorrow == True:
            self.set_data("temperatureMaxi", 0)  # reset temperature maxi

        _LOGGER.info(f"temperatureCalcul={temperatureCalcul}")
        _LOGGER.info(f"filtrationTime={filtrationTime}")

        _LOGGER.info(
            f"filtrationDebut={datetime.fromtimestamp(filtrationDebut).strftime('%H:%M %d-%m-%Y')}"
        )

        if filtrationPauseDebut != filtrationPauseFin:
            _LOGGER.info(
                f"filtrationPauseDebut={datetime.fromtimestamp(filtrationPauseDebut).strftime('%H:%M %d-%m-%Y')}"
            )
            _LOGGER.info(
                f"filtrationPauseFin={datetime.fromtimestamp(filtrationPauseFin).strftime('%H:%M %d-%m-%Y')}"
            )

        _LOGGER.info(
            f"filtrationFin={datetime.fromtimestamp(filtrationFin).strftime('%H:%M %d-%m-%Y')}"
        )

        return

    async def calculateStatusFiltration(self, temperatureWater):
        """Calcul de l'état de la filtration en mode Saison"""

        filtrationTemperature = 0
        filtrationDebut = self.get_data("filtrationDebut", 0)
        filtrationPauseDebut = self.get_data("filtrationPauseDebut", 0)
        filtrationPauseFin = self.get_data("filtrationPauseFin", 0))
        filtrationFin = self.get_data("filtrationFin", 0)

        timeNow = time.time()
        _LOGGER.info(
            f"calculateStatusFiltration: timeNow={datetime.fromtimestamp(timeNow).strftime('%H:%M %d-%m-%Y')}"
        )
        _LOGGER.info(
            f"calculateStatusFiltration: filtrationDebut={datetime.fromtimestamp(filtrationDebut).strftime('%H:%M %d-%m-%Y')}"
        )
        _LOGGER.info(
            f"calculateStatusFiltration: filtrationFin={datetime.fromtimestamp(filtrationFin).strftime('%H:%M %d-%m-%Y')}"
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
                    if self.sondeLocalTechnique == True:
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
                                _LOGGER.debug(f"temperatureMaxi: {temperatureMaxi}")
                                _LOGGER.debug(f"temperatureWater: {temperatureWater}")
                                _LOGGER.debug(
                                    f"(temperatureWater > temperatureMaxi) >> temperatureMaxi=: {temperatureWater}"
                                )

                    else:
                        # Determine la temperature maxi pour le prochain calcul
                        temperatureMaxi = float(self.get_data("temperatureMaxi", 0))

                        if temperatureWater > temperatureMaxi:
                            self.set_data("temperatureMaxi", temperatureWater)
                            _LOGGER.debug(f"temperatureMaxi: {temperatureMaxi}")
                            _LOGGER.debug(f"temperatureWater: {temperatureWater}")
                            _LOGGER.debug(
                                f"(temperatureWater > temperatureMaxi) >> temperatureMaxi=: {temperatureWater}"
                            )

                    # Active la filtration
                    filtrationTemperature = 1

            else:
                # Pas de pause de filtration

                if timeNow >= filtrationDebut and timeNow <= filtrationFin:
                    if self.sondeLocalTechnique == True:
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

                                _LOGGER.debug(f"temperatureMaxi: {temperatureMaxi}")
                                _LOGGER.debug(f"temperatureWater: {temperatureWater}")
                                _LOGGER.debug(
                                    f"(temperatureWater > temperatureMaxi) >> temperatureMaxi=: {temperatureWater}"
                                )

                    else:
                        # Determine la temperature maxi pour le prochain calcul
                        temperatureMaxi = float(self.get_data("temperatureMaxi"))

                        if temperatureWater > temperatureMaxi:
                            self.set_data("temperatureMaxi", temperatureWater)

                            _LOGGER.debug(f"temperatureMaxi: {temperatureMaxi}")
                            _LOGGER.debug(f"temperatureWater: {temperatureWater}")
                            _LOGGER.debug(
                                f"(temperatureWater > temperatureMaxi) >> temperatureMaxi=: {temperatureWater}"
                            )

                    # Active la filtration
                    filtrationTemperature = 1

            if filtrationTemperature == 1:
                if self.disableMarcheForcee == True:
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

        return

    ###############################################################################################################################################################################

    def getHivernage(self):
        if int(self.get_data("hivernageWidgetStatus", 0)) == 1:
            flgHivernage = True
        else:
            flgHivernage = False

        return flgHivernage

    def getStatusHivernage(self, status):
        if int(self.get_data("hivernageWidgetStatus", 0)) == 1:
            status = status + " " + "Hivernage"
        else:
            status = status + " " + "Saison"

        return status

    def calculateTimeFiltrationWithTemperatureHivernage(self, temperatureWater):
        # Filtration (temperature / 3)
        dureeHeures = temperatureWater / 3.0

        # Coefficient d'ajustement (suivant config)
        dureeHeures *= self.coefficientAjustement

        # Au moins 3 heures
        dureeHeures = max(dureeHeures, self.tempsDeFiltrationMinimum)

        return dureeHeures

    def calculateTimeFiltrationHivernage(self, temperatureWater, flgTomorrow):
        temperatureCalcul = float(self.get_data("temperatureMaxi", 0))

        # Si pas de temperature maxi precedente on prend la temperature courante
        if temperatureCalcul == 0 or temperatureCalcul == 0:
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
        if flgTomorrow == True:
            if filtrationPivotSecondes < time.time():
                _LOGGER.info(f"+1 day")
                filtrationPivotSecondes += timedelta(days=1).total_seconds()

        # Repartition de la filtration
        # 2/3 <> 1/3
        filtrationDebut = filtrationPivotSecondes - ((filtrationSecondes / 3.0) * 2.0)
        filtrationFin = filtrationPivotSecondes + (filtrationSecondes / 3.0)

        # Memorise les resultats du calcul
        self.hass.states.async_set("input_text.filtrationTime", filtrationTime)

        display = "* "
        display += datetime.fromtimestamp(filtrationDebut).strftime("%H:%M")
        display += "-"
        display += datetime.fromtimestamp(filtrationFin).strftime("%H:%M")
        display += " : "
        display += str(temperatureCalcul)
        display += "°C"
        self.hass.states.async_set("input_text.filtrationSchedule", display)

        self.set_data("filtrationDebut", int(filtrationDebut))
        self.set_data("filtrationFin", int(filtrationFin))

        self.set_data("calculateStatus", 1)  # 1 >> calcul effectué

        if flgTomorrow == True:
            self.set_data("temperatureMaxi", 0)  # reset temperature maxi

        _LOGGER.info(f"temperatureCalcul={temperatureCalcul}")
        _LOGGER.info(f"filtrationTime={filtrationTime}")

        _LOGGER.info(
            f"filtrationDebut={datetime.fromtimestamp(filtrationDebut).strftime('%H:%M %d-%m-%Y')}"
        )
        _LOGGER.info(
            f"filtrationFin={datetime.fromtimestamp(filtrationFin).strftime('%H:%M %d-%m-%Y')}"
        )

    async def calculateStatusFiltrationHivernage(
        self, temperatureWater, temperatureOutdoor
    ):
        """Calcul de l'état de la filtration en mode Saison"""

        filtrationHivernage = 0

        filtrationDebut = self.get_data("filtrationDebut", 0)
        filtrationFin = self.get_data("filtrationFin", 0)

        timeNow = time.time()
        _LOGGER.info(
            f"calculateStatusFiltration: timeNow={datetime.fromtimestamp(timeNow).strftime('%H:%M %d-%m-%Y')}"
        )
        _LOGGER.info(
            f"calculateStatusFiltration: filtrationDebut={datetime.fromtimestamp(filtrationDebut).strftime('%H:%M %d-%m-%Y')}"
        )
        _LOGGER.info(
            f"calculateStatusFiltration: filtrationFin={datetime.fromtimestamp(filtrationFin).strftime('%H:%M %d-%m-%Y')}"
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
                if self.sondeLocalTechnique == True:
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

                            _LOGGER.debug(f"temperatureMaxi: {temperatureMaxi}")
                            _LOGGER.debug(f"temperatureWater: {temperatureWater}")
                            _LOGGER.debug(
                                f"(temperatureWater > temperatureMaxi) >> temperatureMaxi=: {temperatureWater}"
                            )

                else:
                    # Determine la temperature maxi pour le prochain calcul
                    temperatureMaxi = float(self.get_data("temperatureMaxi"))

                    if temperatureWater > temperatureMaxi:
                        self.set_data("temperatureMaxi", temperatureWater)

                        _LOGGER.debug(f"temperatureMaxi: {temperatureMaxi}")
                        _LOGGER.debug(f"temperatureWater: {temperatureWater}")
                        _LOGGER.debug(
                            f"(temperatureWater > temperatureMaxi) >> temperatureMaxi=: {temperatureWater}"
                        )

                # Active la filtration
                filtrationHivernage = 1

            if filtrationHivernage == 1:
                if self.disableMarcheForcee == True:
                    if int(self.get_data("marcheForcee", 0)) == 1:
                        self.set_data("marcheForcee", 0)

                if int(self.get_data("calculateStatus", 0)) != 0:
                    self.set_data("calculateStatus", 0)

            calculateStatus = int(self.get_data("calculateStatus", 0))

            if timeNow > filtrationFin and calculateStatus == 0:
                # On est apres la plage de filtration, relancer le calcul pour la plage de demain
                self.calculateTimeFiltrationHivernage(temperatureWater, True)
                self.hass.states.async_set(
                    "input_number.temperatureDisplay", temperatureWater
                )

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
                    f"Arret securité gel sur temperature exterieure > {self.temperatureSecurite + self.temperatureHysteresis}"
                )

                filtrationHivernageSecurite = 0

        elif temperatureOutdoor < self.temperatureSecurite:
            _LOGGER.debug(
                f"Securité gel sur temperature exterieure < {self.temperatureSecurite}"
            )

            filtrationHivernageSecurite = 1

        self.set_data("filtrationHivernageSecurite", filtrationHivernageSecurite)

        # Securité gel sur temperature exterieure < temperatureSecurite
        if filtrationHivernageSecurite != 0:
            filtrationHivernage = 1

        # 5mn toutes les 3H
        if self.filtration5mn3h == True:
            currentTime = datetime.now().strftime("%H%M")

            if "0200" <= currentTime <= "0205":
                filtrationHivernage = 1
            elif "0500" <= currentTime <= "0505":
                filtrationHivernage = 1
            elif "0800" <= currentTime <= "0805":
                filtrationHivernage = 1
            elif "1100" <= currentTime <= "1105":
                filtrationHivernage = 1
            elif "1400" <= currentTime <= "1405":
                filtrationHivernage = 1
            elif "1700" <= currentTime <= "1705":
                filtrationHivernage = 1
            elif "2000" <= currentTime <= "2005":
                filtrationHivernage = 1
            elif "2300" <= currentTime <= "2305":
                filtrationHivernage = 1

        if int(self.get_data("filtrationHivernage", 0)) != filtrationHivernage:
            self.set_data("filtrationHivernage", filtrationHivernage)

        if int(self.get_data("filtrationTemperature", 0)) != 0:
            self.set_data("filtrationTemperature", 0)

    ###############################################################################################################################################################################

    def getTemperatureWater(self) -> float:
        """Récupére la température de l'eau"""

        temperatureState = self.hass.states.get(self.temperatureWater)

        if temperatureState is None:
            _LOGGER.error(f"Temperature water {self.temperatureWater} not found")
            return 0.0

        try:
            temperatureWater = float(temperatureState.state)
        except ValueError:
            _LOGGER.error(f"Invalid temperature value: {temperatureState.state}")
            return 0.0

        return temperatureWater

    def getTemperatureOutdoor(self) -> float:
        """Récupére la température de l'air"""

        temperatureState = self.hass.states.get(self.temperatureOutdoor)

        if temperatureState is None:
            _LOGGER.error(f"Temperature air {self.temperatureOutdoor} not found")
            return 0.0

        try:
            temperatureWater = float(temperatureState.state)
        except ValueError:
            _LOGGER.error(f"Invalid temperature value: {temperatureState.state}")
            return 0.0

        return temperatureWater

    def getLeverSoleil(self) -> str:
        """Récupére l'heure de lever du soleil"""

        leverSoleilState = self.hass.states.get(self.leverSoleil)

        if leverSoleilState is None:
            _LOGGER.error(f"Lever du soleil {self.leverSoleil} not found")
            return str("06:00")

        # Extraire l'heure de lever du soleil à partir de l'état
        sunriseTimeStr = leverSoleilState.state

        # Convertir la chaîne de caractères ISO 8601 en objet datetime
        sunriseTime = datetime.fromisoformat(sunriseTimeStr)

        # Convertir l'objet datetime en chaîne de caractères dans le format "06:00"
        return sunriseTime.strftime("%H:%M")

    ###############################################################################################################################################################################

    async def trackButtonSurpresseur(self):
        """Ecoute le bouton 'Surpresseur'"""

        # TODO: tester "self.buttonSurpresseur"

        async_track_state_change(
            self.hass, self.buttonSurpresseur, self.handleButtonSurpresseur
        )

        return

    async def handleButtonSurpresseur(self, entity_id, old_state, new_state):
        if self.buttonSurpresseurFirstCall:
            self.buttonSurpresseurFirstCall = False
            return

        await self.executeSurpresseurOn()

        return

    async def executeSurpresseurOn(self):
        """Lance le surpresseur"""

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
            self.hass.states.async_set("input_text.surpresseurStatus", display)

            self.set_data("filtrationSurpresseur", 1)
            await self.activatingDevices()

        await self.startSecondCron()

        return

    ###############################################################################################################################################################################

    async def trackButtonLavage(self):
        """Ecoute le bouton 'Lavage'"""

        # TODO: tester "self.buttonLavage"

        async_track_state_change(self.hass, self.buttonLavage, self.handleButtonLavage)

        return

    async def handleButtonLavage(self, entity_id, old_state, new_state):
        if self.buttonLavageFirstCall:
            self.buttonLavageFirstCall = False
            return

        await self.executeFiltreSableLavageOn()

        return

    async def executeFiltreSableLavageOn(self):
        """Lance le lavage du filtre à sable"""

        if self.get_data("filtrationSurpresseur", 0) == 0:
            lavageState = int(self.get_data("filtrationLavageEtat", 0))

            if lavageState == 0:
                # Arrêt, mettre la vanne sur la position lavage
                self.set_data("filtrationLavageEtat", 1)
                self.hass.states.async_set(
                    "input_text.filtreSableLavageStatus", "Arrêt, position lavage"
                )
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
                self.hass.states.async_set(
                    "input_text.filtreSableLavageStatus", display
                )
                self.set_data("filtrationLavage", 2)
                await self.activatingDevices()

            elif lavageState == 2:
                # Arrêt, mettre la vanne sur la position rinçage
                self.set_data("filtrationLavageEtat", 3)
                self.hass.states.async_set(
                    "input_text.filtreSableLavageStatus", "Arrêt, position rinçage"
                )
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
                self.hass.states.async_set(
                    "input_text.filtreSableLavageStatus", display
                )
                self.set_data("filtrationLavage", 2)
                await self.activatingDevices()

            elif lavageState == 4:
                # Arrêt, mettre la vanne sur la position filtration
                self.set_data("filtrationLavageEtat", 5)
                self.hass.states.async_set(
                    "input_text.filtreSableLavageStatus", "Arrêt, position filtration"
                )
                self.set_data("filtrationLavage", 1)
                await self.activatingDevices()

            elif lavageState == 5:
                # Arrêté
                self.set_data("filtrationLavageEtat", 0)
                self.hass.states.async_set(
                    "input_text.filtreSableLavageStatus", "Arrêté"
                )
                self.set_data("filtrationLavage", 0)
                await self.activatingDevices()

                await self.stopSecondCron()

    ###############################################################################################################################################################################

    async def trackButtonStop(self):
        """Ecoute le bouton 'Stop'"""

        # TODO: tester "self.buttonStop"

        async_track_state_change(self.hass, self.buttonStop, self.handleButtonStop)

        return

    async def handleButtonStop(self, entity_id, old_state, new_state):
        if self.buttonStopFirstCall:
            self.buttonStopFirstCall = False
            return

        await self.executePoolStop()

        return

    async def executePoolStop(self):
        """Arrête le surpresseur / lavage filtre"""

        await self.stopSecondCron()

        if int(self.get_data("filtrationSurpresseur", 0)) == 1:
            self.set_data("filtrationSurpresseur", 0)
            self.hass.states.async_set("input_text.surpresseurStatus", "Arrêté")
            await self.activatingDevices()

        if int(self.get_data("filtrationLavageEtat", 0)) != 0:
            self.set_data("filtrationLavageEtat", 0)
            self.set_data("filtrationLavage", 0)
            self.hass.states.async_set("input_text.filtreSableLavageStatus", "Arrêté")
            await self.activatingDevices()

        return

    ###############################################################################################################################################################################

    async def trackButtonReset(self):
        """Ecoute le bouton 'Reset'"""

        # TODO: tester "self.buttonReset"

        async_track_state_change(self.hass, self.buttonReset, self.handleButtonReset)

        return

    async def handleButtonReset(self, entity_id, old_state, new_state):
        if self.buttonResetFirstCall:
            self.buttonResetFirstCall = False
            return

        await self.executeResetCalcul()

        return

    async def executeResetCalcul(self):
        """Reinitialise le calcul"""

        if self.getHivernage() == True:
            self.set_data("temperatureMaxi", 0)  # reset temperature maxi

            temperatureWater = self.getTemperatureWater()
            temperatureOutdoor = self.getTemperatureOutdoor()

            self.calculateTimeFiltrationHivernage(temperatureWater, False)

            # Verifie si la plage calculée est passée
            filtrationFin = self.get_data("filtrationFin", 0)
            timeNow = time.time()

            _LOGGER.debug(
                f"filtrationFin={datetime.fromtimestamp(filtrationFin).strftime('%H:%M %d-%m-%Y')}"
            )
            _LOGGER.info(
                f"timeNow={datetime.fromtimestamp(time.time()).strftime('%H:%M %d-%m-%Y')}"
            )

            if timeNow > filtrationFin:
                # On est apres la plage de filtration, relancer le calcul pour la plage de demain
                self.calculateTimeFiltrationHivernage(temperatureWater, True)

            await self.calculateStatusFiltrationHivernage(
                temperatureWater, temperatureOutdoor
            )

        else:
            self.set_data("temperatureMaxi", 0)  # reset temperature maxi

            temperatureWater = self.getTemperatureWater()
            self.calculateTimeFiltration(temperatureWater, False)

            # Verifie si la plage calculée est passée
            filtrationFin = self.get_data("filtrationFin", 0)
            timeNow = time.time()

            _LOGGER.debug(
                f"filtrationFin={datetime.fromtimestamp(filtrationFin).strftime('%H:%M %d-%m-%Y')}"
            )
            _LOGGER.info(
                f"timeNow={datetime.fromtimestamp(time.time()).strftime('%H:%M %d-%m-%Y')}"
            )

            if timeNow > filtrationFin:
                # On est apres la plage de filtration, relancer le calcul pour la plage de demain
                self.calculateTimeFiltration(temperatureWater, True)

            await self.calculateStatusFiltration(temperatureWater)

        await self.activatingDevices()

        return

    ###############################################################################################################################################################################

    async def refreshFiltration(self):
        """Rafraichi l'état de la filtration"""

        filtrationState = self.hass.states.get(self.filtration)

        if filtrationState is None:
            _LOGGER.error(f"Filtration {self.filtration} not found")
            return

        if filtrationState.state == "on":
            await self.filtrationOn(True)

        elif filtrationState.state == "off":
            await self.filtrationStop(True)

        return

    async def filtrationOn(self, repeat=False):
        """Active la filtration"""

        filtrationState = self.hass.states.get(self.filtration)

        if filtrationState is None:
            _LOGGER.error(f"Filtration {self.filtration} not found")
            return

        if not repeat and filtrationState.state == "on":
            return

        # Active la filtration
        await self.hass.services.async_call(
            "input_boolean",  # switch / input_boolean
            "turn_on",
            {"entity_id": self.filtration},
        )

        self.hass.states.async_set("input_text.filtrationStatus", "Actif")

        return

    async def filtrationStop(self, repeat=False):
        """Arrête la filtration"""

        filtrationState = self.hass.states.get(self.filtration)

        if filtrationState is None:
            _LOGGER.error(f"Filtration {self.filtration} not found")
            return

        if not repeat and filtrationState.state == "off":
            return

        # Arrête la filtration
        await self.hass.services.async_call(
            "input_boolean",  # switch / input_boolean
            "turn_off",
            {"entity_id": self.filtration},
        )

        self.hass.states.async_set("input_text.filtrationStatus", "Arrêté")

        return

    ###############################################################################################################################################################################

    async def refreshSurpresseur(self):
        """Rafraichi l'état du surpresseur"""

        surpresseurState = self.hass.states.get(self.surpresseur)

        if surpresseurState is None:
            _LOGGER.error(f"Surpresseur {self.surpresseur} not found")
            return

        if surpresseurState.state == "on":
            await self.surpresseurOn(True)

        elif surpresseurState.state == "off":
            await self.surpresseurStop(True)

        return

    def getStateSurpresseur(self) -> bool:
        """Obtient l'état du surpresseur"""

        surpresseurState = self.hass.states.get(self.surpresseur)

        if surpresseurState is None:
            _LOGGER.error(f"Surpresseur {self.surpresseur} not found")
            return False

        if surpresseurState.state == "on":
            return True
        else:
            return False

    async def surpresseurOn(self, repeat=False):
        """Active le surpresseur"""

        surpresseurState = self.hass.states.get(self.surpresseur)

        if surpresseurState is None:
            _LOGGER.error(f"Surpresseur {self.surpresseur} not found")
            return

        if not repeat and surpresseurState.state == "on":
            return

        # Active le surpresseur
        await self.hass.services.async_call(
            "input_boolean",  # switch / input_boolean
            "turn_on",
            {"entity_id": self.surpresseur},
        )

        # self.hass.states.async_set("input_text.surpresseurStatus", "Actif")

        return

    async def surpresseurStop(self, repeat=False):
        """Arrête le surpresseur"""

        surpresseurState = self.hass.states.get(self.surpresseur)

        if surpresseurState is None:
            _LOGGER.error(f"Surpresseur {self.surpresseur} not found")
            return

        if not repeat and surpresseurState.state == "off":
            return

        # Arrête le surpresseur
        await self.hass.services.async_call(
            "input_boolean",  # switch / input_boolean
            "turn_off",
            {"entity_id": self.surpresseur},
        )

        # self.hass.states.async_set("input_text.surpresseurStatus", "Arrêté")

        return

    ###############################################################################################################################################################################

    async def refreshTraitement(self):
        """Rafraichi l'état du traitement"""

        traitementState = self.hass.states.get(self.traitement)

        if traitementState is None:
            _LOGGER.error(f"Traitement {self.traitement} not found")
            return

        if traitementState.state == "on":
            await self.traitementOn(True)

        elif traitementState.state == "off":
            await self.traitementStop(True)

        return

    def getStateTraitement(self) -> bool:
        """Obtient l'état du traitement"""

        traitementState = self.hass.states.get(self.traitement)

        if traitementState is None:
            _LOGGER.error(f"Traitement {self.traitement} not found")
            return False

        if traitementState.state == "on":
            return True
        else:
            return False

    async def traitementOn(self, repeat=False):
        """Active le traitement"""

        traitementState = self.hass.states.get(self.traitement)

        if traitementState is None:
            _LOGGER.error(f"Traitement {self.traitement} not found")
            return

        if not repeat and traitementState.state == "on":
            return

        # Active le traitement
        await self.hass.services.async_call(
            "input_boolean",  # switch / input_boolean
            "turn_on",
            {"entity_id": self.traitement},
        )

        # self.hass.states.async_set("input_text.traitementStatus", "Actif")

        return

    async def traitementStop(self, repeat=False):
        """Arrête le traitement"""

        traitementState = self.hass.states.get(self.traitement)

        if traitementState is None:
            _LOGGER.error(f"Traitement {self.traitement} not found")
            return

        if not repeat and traitementState.state == "off":
            return

        # Arrête le traitement
        await self.hass.services.async_call(
            "input_boolean",  # switch / input_boolean
            "turn_off",
            {"entity_id": self.traitement},
        )

        # self.hass.states.async_set("input_text.traitementStatus", "Arrêté")

        return

    ###############################################################################################################################################################################

    async def trackButtonActif(self):
        """Ecoute le bouton 'Actif'"""

        # TODO: tester "self.buttonActif"

        async_track_state_change(self.hass, self.buttonActif, self.handleButtonActif)

        return

    async def handleButtonActif(self, entity_id, old_state, new_state):
        if self.buttonActifFirstCall:
            self.buttonActifFirstCall = False
            return

        self.set_data("marcheForcee", 1)
        self.set_data("arretTotal", 0)
        await self.activatingDevices()

        return

    ###############################################################################################################################################################################

    async def trackButtonAuto(self):
        """Ecoute le bouton 'Auto'"""

        # TODO: tester "self.buttonAuto"

        async_track_state_change(self.hass, self.buttonAuto, self.handleButtonAuto)

        return

    async def handleButtonAuto(self, entity_id, old_state, new_state):
        if self.buttonAutoFirstCall:
            self.buttonAutoFirstCall = False
            return

        self.set_data("marcheForcee", 0)
        self.set_data("arretTotal", 0)
        await self.activatingDevices()

        return

    ###############################################################################################################################################################################

    async def trackButtonInactif(self):
        """Ecoute le bouton 'Inactif'"""

        # TODO: tester "self.buttonInactif"

        async_track_state_change(
            self.hass, self.buttonInactif, self.handleButtonInactif
        )

        return

    async def handleButtonInactif(self, entity_id, old_state, new_state):
        if self.buttonInactifFirstCall:
            self.buttonInactifFirstCall = False
            return

        self.set_data("marcheForcee", 0)
        self.set_data("arretTotal", 1)
        await self.activatingDevices()

        return

    ###############################################################################################################################################################################

    async def trackButtonSaison(self):
        """Ecoute le bouton 'Inactif'"""

        # TODO: tester "self.buttonSaison"

        async_track_state_change(self.hass, self.buttonSaison, self.handleButtonSaison)

        return

    async def handleButtonSaison(self, entity_id, old_state, new_state):
        if self.buttonSaisonFirstCall:
            self.buttonSaisonFirstCall = False
            return

        self.set_data("hivernageWidgetStatus", 0)
        await self.activatingDevices()
        await self.executeResetCalcul()

        return

    ###############################################################################################################################################################################

    async def trackButtonHivernage(self):
        """Ecoute le bouton 'Inactif'"""

        # TODO: tester "self.buttonHivernage"

        async_track_state_change(
            self.hass, self.buttonHivernage, self.handleButtonHivernage
        )

        return

    async def handleButtonHivernage(self, entity_id, old_state, new_state):
        if self.buttonHivernageFirstCall:
            self.buttonHivernageFirstCall = False
            return

        self.set_data("hivernageWidgetStatus", 1)
        await self.activatingDevices()
        await self.executeResetCalcul()

        return

    ###############################################################################################################################################################################

    async def async_initialize(self):
        """Initialise PoolController by loading data from store."""

        raw_data = await self.store.async_load()

        if raw_data:
            self.data = raw_data
            _LOGGER.info("Loaded data from store: %s", self.data)
        else:
            _LOGGER.info("No data found in store")

        self.initialized = True

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_save_data)

        return

    async def async_save_data(self, event=None):
        """Save the current data to the store."""

        if self.initialized:
            await self.store.async_save(self.data)

            if event != None:
                _LOGGER.info("Saved data to store: %s", self.data)

    def set_data(self, key, value):
        oldValue = self.data.get(key)
        self.data[key] = value

        if oldValue != value:
            self.hass.async_create_task(self.async_save_data())

    def get_data(self, key, default=None):
        return self.data.get(key, default)


###############################################################################################################################################################################
###############################################################################################################################################################################


async def async_setup(hass: HomeAssistant, config: dict):
    """Initialisation du plugin"""

    pool = PoolController(hass, config[DOMAIN])
    hass.data[DOMAIN] = pool

    await pool.async_initialize()

    await pool.startFirstCron()

    await pool.trackButtonReset()
    await pool.trackButtonSurpresseur()
    await pool.trackButtonLavage()
    await pool.trackButtonStop()
    await pool.trackButtonActif()
    await pool.trackButtonAuto()
    await pool.trackButtonInactif()
    await pool.trackButtonHivernage()
    await pool.trackButtonSaison()

    return True
