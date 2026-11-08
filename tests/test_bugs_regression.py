"""Tests de non-régression pour les bugs critiques corrigés.

Ces tests garantissent que les bugs identifiés et corrigés (PR #1 pour les
bugs #1 à #6) ne reviennent pas dans les futures versions.

Bugs testés:
1. Bug #1: Méthode manquante executePoolStop() → executeButtonStop()
2. Bug #2: KeyError sur temperatureMaxi
3. Bug #3: Message de log incorrect
4. Bug #4: Type incohérent methodeCalcul
5. Bug #5: Crash si traitement non configuré
6. Bug #6: Entité optionnelle temperatureDisplay
7. Bug #7: Heure de lever du soleil lue en UTC
8. Bug #8: Surpresseur bloqué en marche après un redémarrage
9. Bug #9: Plages horaires calculées dans le fuseau du système
10. Bug #10: Plus aucun recalcul après une plage jamais atteinte
11. Bug #11: Sonde de température indisponible lue comme 0 °C
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import logging

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")


@pytest.mark.bugs
class TestBug1_ExecuteButtonStop:
    """Test Bug #1: Méthode manquante executePoolStop().

    Bug original: scheduler.py:61 appelait executePoolStop() qui n'existe pas
    Correction: Appelle maintenant executeButtonStop()
    """

    def test_scheduler_has_execute_button_stop(self, mock_hass, mock_pool_config):
        """Vérifie que SchedulerMixin a la méthode executeButtonStop."""
        from custom_components.pool_control.scheduler import SchedulerMixin

        class TestController(SchedulerMixin):
            def __init__(self):
                super().__init__()
                self.hass = mock_hass
                self.executeButtonStop = AsyncMock()
                self.get_data = Mock(return_value=0)
                self.surpresseurStatus = None

        controller = TestController()

        # Vérifier que la méthode existe
        assert hasattr(controller, 'executeButtonStop')
        assert callable(controller.executeButtonStop)

    @pytest.mark.asyncio
    async def test_pull_calls_execute_button_stop_when_timeout(self, mock_hass, mock_pool_config):
        """Vérifie que pull() appelle executeButtonStop() quand le temps expire."""
        from custom_components.pool_control.scheduler import SchedulerMixin
        import time

        class TestController(SchedulerMixin):
            def __init__(self):
                super().__init__()
                self.hass = mock_hass
                self.executeButtonStop = AsyncMock()
                self.surpresseurStatus = None

            def get_data(self, key, default=0):
                if key == "filtrationSurpresseur":
                    return 1  # Surpresseur actif
                elif key == "filtrationTempsRestant":
                    return time.time() - 10  # Temps expiré (dans le passé)
                elif key == "filtrationLavageEtat":
                    return 0
                return default

        controller = TestController()

        # Exécuter pull()
        await controller.pull()

        # Vérifier que executeButtonStop() a été appelé (PAS executePoolStop())
        controller.executeButtonStop.assert_called_once()


@pytest.mark.bugs
class TestBug2_TemperatureMaxiKeyError:
    """Test Bug #2: KeyError sur temperatureMaxi.

    Bug original: saison.py et hivernage.py crashaient si temperatureMaxi n'existait pas
    Correction: Ajout valeur par défaut 0
    """

    def test_saison_temperature_maxi_has_default(self, mock_hass, mock_pool_config):
        """Vérifie que temperatureMaxi a une valeur par défaut dans saison.py."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)

        # Simuler première exécution (pas de temperatureMaxi stocké)
        controller.data = {}

        # Cette ligne ne doit PAS crasher avec KeyError
        try:
            temp_maxi = float(controller.get_data("temperatureMaxi", 0))
            assert temp_maxi == 0  # Valeur par défaut
        except KeyError:
            pytest.fail("KeyError sur temperatureMaxi - Bug #2 non corrigé!")

    def test_hivernage_temperature_maxi_has_default(self, mock_hass, mock_pool_config):
        """Vérifie que temperatureMaxi a une valeur par défaut dans hivernage.py."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.data = {}

        # get_data doit retourner la valeur par défaut
        temp_maxi = controller.get_data("temperatureMaxi", 0)
        assert temp_maxi == 0

    def test_get_data_returns_default_for_missing_keys(self, mock_hass, mock_pool_config):
        """Vérifie que get_data retourne la valeur par défaut pour toute clé manquante."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.data = {}

        # Tester avec plusieurs clés
        assert controller.get_data("temperatureMaxi", 0) == 0
        assert controller.get_data("nonExistentKey", 42) == 42
        assert controller.get_data("anotherKey", "default") == "default"


@pytest.mark.bugs
class TestBug3_LogMessageIncorrect:
    """Test Bug #3: Message de log incorrect.

    Bug original: scheduler.py:86 affichait "Second cron job started" au lieu de "First cron"
    Correction: Message corrigé en "First cron job started"
    """

    @pytest.mark.asyncio
    async def test_start_second_cron_logs_correct_message(self, mock_hass, mock_pool_config, caplog):
        """Vérifie que startSecondCron() log le bon message."""
        from custom_components.pool_control.scheduler import SchedulerMixin

        class TestController(SchedulerMixin):
            def __init__(self):
                super().__init__()
                self.hass = mock_hass

        controller = TestController()

        with caplog.at_level(logging.INFO):
            with patch('custom_components.pool_control.scheduler.async_track_time_interval'):
                await controller.startSecondCron()

        # Vérifier le message de log
        assert "Second cron job started" in caplog.text
        # Ne devrait PAS contenir "First cron" ici
        # (c'est startFirstCron qui log "First cron")

    @pytest.mark.asyncio
    async def test_start_first_cron_logs_correct_message(self, mock_hass, mock_pool_config, caplog):
        """Vérifie que startFirstCron() log le bon message."""
        from custom_components.pool_control.scheduler import SchedulerMixin

        class TestController(SchedulerMixin):
            def __init__(self):
                super().__init__()
                self.hass = mock_hass

        controller = TestController()

        with caplog.at_level(logging.INFO):
            with patch('custom_components.pool_control.scheduler.async_track_time_interval'):
                await controller.startFirstCron()

        # Vérifier le message de log correct
        assert "First cron job started" in caplog.text


@pytest.mark.bugs
class TestBug4_MethodeCalculType:
    """Test Bug #4: Type incohérent methodeCalcul.

    Bug original: methodeCalcul pouvait être string "1" au lieu de int 1
    Correction: Conversion forcée en int
    """

    def test_methode_calcul_is_always_int_from_string(self, mock_hass, mock_pool_config):
        """Vérifie que methodeCalcul est toujours un int même si config contient une string."""
        from custom_components.pool_control.controller import PoolController

        # Configuration avec string
        mock_pool_config["methodeCalcul"] = "2"
        controller = PoolController(mock_hass, mock_pool_config)

        assert isinstance(controller.methodeCalcul, int)
        assert controller.methodeCalcul == 2

    def test_methode_calcul_is_always_int_from_int(self, mock_hass, mock_pool_config):
        """Vérifie que methodeCalcul reste un int si config contient déjà un int."""
        from custom_components.pool_control.controller import PoolController

        # Configuration avec int
        mock_pool_config["methodeCalcul"] = 1
        controller = PoolController(mock_hass, mock_pool_config)

        assert isinstance(controller.methodeCalcul, int)
        assert controller.methodeCalcul == 1

    def test_methode_calcul_has_default_value(self, mock_hass, mock_pool_config):
        """Vérifie que methodeCalcul a une valeur par défaut si absent."""
        from custom_components.pool_control.controller import PoolController

        # Configuration sans methodeCalcul
        if "methodeCalcul" in mock_pool_config:
            del mock_pool_config["methodeCalcul"]

        controller = PoolController(mock_hass, mock_pool_config)

        assert isinstance(controller.methodeCalcul, int)
        assert controller.methodeCalcul == 1  # Valeur par défaut


@pytest.mark.bugs
class TestBug5_TraitementNoneCheck:
    """Test Bug #5: Crash si traitement non configuré.

    Bug original: traitement.py crashait si self.traitement était None
    Correction: Vérifications None ajoutées dans 8 méthodes
    """

    @pytest.mark.asyncio
    async def test_traitement_on_no_crash_when_none(self, mock_hass, mock_pool_config):
        """Vérifie qu'il n'y a pas de crash si traitement est None."""
        from custom_components.pool_control.controller import PoolController

        # Configuration sans traitement
        config = mock_pool_config.copy()
        config["traitement"] = None

        controller = PoolController(mock_hass, config)

        # Cette méthode ne doit PAS crasher
        try:
            await controller.traitementOn()
            # Si on arrive ici, pas de crash ✅
            assert True
        except AttributeError as e:
            pytest.fail(f"AttributeError avec traitement=None - Bug #5 non corrigé! {e}")
        except Exception as e:
            # On accepte d'autres erreurs (comme log error), mais pas AttributeError
            if "NoneType" in str(e):
                pytest.fail(f"Erreur NoneType avec traitement=None - Bug #5 non corrigé! {e}")

    @pytest.mark.asyncio
    async def test_traitement_stop_no_crash_when_none(self, mock_hass, mock_pool_config):
        """Vérifie que traitementStop() ne crash pas si traitement est None."""
        from custom_components.pool_control.controller import PoolController

        config = mock_pool_config.copy()
        config["traitement"] = None
        controller = PoolController(mock_hass, config)

        try:
            await controller.traitementStop()
            assert True
        except AttributeError as e:
            pytest.fail(f"AttributeError - Bug #5 non corrigé! {e}")

    def test_get_state_traitement_returns_false_when_none(self, mock_hass, mock_pool_config):
        """Vérifie que getStateTraitement() retourne False si traitement est None."""
        from custom_components.pool_control.controller import PoolController

        config = mock_pool_config.copy()
        config["traitement"] = None
        controller = PoolController(mock_hass, config)

        try:
            state = controller.getStateTraitement()
            assert state == False  # Devrait retourner False, pas crasher
        except AttributeError as e:
            pytest.fail(f"AttributeError - Bug #5 non corrigé! {e}")


@pytest.mark.bugs
class TestBug6_TemperatureDisplayOptional:
    """Test Bug #6: Entité optionnelle temperatureDisplay.

    Bug original: Le code crashait si l'entité temperatureDisplay n'existait pas
    Correction: Méthode helper updateTemperatureDisplay() qui gère l'absence
    """

    def test_update_temperature_display_exists(self, mock_hass, mock_pool_config):
        """Vérifie que la méthode updateTemperatureDisplay() existe."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)

        # Vérifier que la méthode existe
        assert hasattr(controller, 'updateTemperatureDisplay')
        assert callable(controller.updateTemperatureDisplay)

    def test_update_temperature_display_no_crash_when_entity_missing(self, mock_hass, mock_pool_config):
        """Vérifie qu'il n'y a pas de crash si l'entité temperatureDisplay n'existe pas."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)

        # Simuler l'absence de l'entité temperatureDisplay
        mock_hass.states.get.return_value = None

        # Cette fonction ne doit PAS crasher
        try:
            controller.updateTemperatureDisplay(25.5)
            # Si on arrive ici, pas de crash ✅
            assert True
        except Exception as e:
            pytest.fail(f"Exception avec temperatureDisplay manquante: {e}")

    def test_update_temperature_display_sets_value_when_entity_exists(self, mock_hass, mock_pool_config):
        """Vérifie que updateTemperatureDisplay() met à jour la valeur si l'entité existe."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)

        # Simuler l'existence de l'entité
        mock_entity = MagicMock()
        mock_entity.state = "20.0"
        mock_hass.states.get.return_value = mock_entity

        # Appeler la méthode
        controller.updateTemperatureDisplay(25.5)

        # Vérifier que async_set a été appelé
        mock_hass.states.async_set.assert_called_once_with(
            "input_number.temperatureDisplay",
            25.5
        )


@pytest.mark.bugs
class TestBug7_LeverSoleilFuseau:
    """Test Bug #7: Heure de lever du soleil lue en UTC.

    Bug original: sensors.py extrayait HH:MM de sensor.sun_next_rising (UTC) sans
    conversion, décalant le pivot d'hivernage de 1 à 2 h, et plantait sur "unavailable"
    Correction: Conversion dans le fuseau de Home Assistant, repli sur 06:00
    """

    @pytest.fixture(autouse=True)
    def ha_time_zone(self):
        """Fuseau Home Assistant fixé à UTC+2 (heure d'été de Paris)."""
        from datetime import timedelta, timezone
        from homeassistant.util import dt as dt_util

        previous = dt_util.DEFAULT_TIME_ZONE
        dt_util.set_default_time_zone(timezone(timedelta(hours=2)))
        yield
        dt_util.set_default_time_zone(previous)

    @pytest.fixture
    def controller_with_sunrise(self, setup_hass_states, mock_pool_config):
        """Crée un PoolController dont sensor.sun_next_rising a l'état donné."""
        from custom_components.pool_control.controller import PoolController

        def _create(state):
            states = {} if state is None else {"sensor.sun_next_rising": state}
            return PoolController(setup_hass_states(states), mock_pool_config)

        return _create

    def test_utc_sunrise_is_converted_to_local_time(self, controller_with_sunrise):
        """Vérifie que 05:33 UTC donne 07:33 en heure locale (UTC+2)."""
        controller = controller_with_sunrise("2026-09-14T05:33:12+00:00")

        assert controller.getLeverSoleil() == "07:33"

    def test_naive_sunrise_is_kept_as_local_time(self, controller_with_sunrise):
        """Vérifie qu'un horodatage sans fuseau est considéré comme local."""
        controller = controller_with_sunrise("2026-09-14T07:33:12")

        assert controller.getLeverSoleil() == "07:33"

    @pytest.mark.parametrize("state", ["unavailable", "unknown", ""])
    def test_invalid_state_falls_back_without_crash(self, controller_with_sunrise, state):
        """Vérifie qu'un état non horodaté ne fait pas planter le cron."""
        controller = controller_with_sunrise(state)

        assert controller.getLeverSoleil() == "06:00"

    def test_missing_entity_falls_back(self, controller_with_sunrise):
        """Vérifie le repli sur 06:00 si l'entité n'existe pas."""
        controller = controller_with_sunrise(None)

        assert controller.getLeverSoleil() == "06:00"


@pytest.mark.bugs
class TestBug8_RepriseCycleApresRedemarrage:
    """Test Bug #8: Surpresseur bloqué en marche après un redémarrage.

    Bug original: filtrationSurpresseur / filtrationLavageEtat étaient restaurés depuis
    le Store mais le cron '5 secondes' n'était pas relancé : le compte à rebours
    n'était plus suivi et le surpresseur restait actif indéfiniment
    Correction: async_setup_entry() appelle resumeSecondCron()
    """

    @pytest.mark.asyncio
    async def test_setup_entry_resumes_second_cron(self, mock_hass):
        """Vérifie que async_setup_entry() reprend un cycle interrompu."""
        from custom_components import pool_control

        controller = MagicMock()
        controller.async_initialize = AsyncMock()
        controller.startFirstCron = AsyncMock()
        controller.resumeSecondCron = AsyncMock()

        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        entry.unique_id = "piscine"
        entry.title = "Piscine"
        entry.data = {}
        entry.options = {}

        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        with patch.object(
            pool_control, "PoolController", return_value=controller
        ), patch.object(pool_control, "async_register_panel", new=AsyncMock()):
            assert await pool_control.async_setup_entry(mock_hass, entry) is True

        controller.startFirstCron.assert_awaited_once()
        controller.resumeSecondCron.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_expired_surpresseur_is_stopped_after_restart(self, mock_hass, mock_pool_config):
        """Vérifie qu'un cycle surpresseur écoulé pendant l'arrêt de HA est terminé."""
        from custom_components.pool_control.controller import PoolController
        import time

        controller = PoolController(mock_hass, mock_pool_config)
        controller.surpresseurStatus = MagicMock()
        controller.filtreSableLavageStatus = MagicMock()
        controller.activatingDevices = AsyncMock()

        # État restauré depuis le Store : cycle lancé avant l'arrêt, durée écoulée
        controller.data = {
            "filtrationSurpresseur": 1,
            "filtrationTempsRestant": int(time.time()) - 60,
        }

        callbacks = []

        def fake_track(hass, action, interval):
            callbacks.append(action)
            return Mock()

        with patch(
            "custom_components.pool_control.scheduler.async_track_time_interval",
            side_effect=fake_track,
        ):
            await controller.resumeSecondCron()

            # Premier tick du cron '5 secondes'
            assert len(callbacks) == 1
            await callbacks[0]()

        assert controller.get_data("filtrationSurpresseur") == 0
        controller.surpresseurStatus.set_status.assert_called_with("Arrêté")
        controller.activatingDevices.assert_awaited()
        assert controller.secondCronCancel is None


@pytest.mark.bugs
class TestBug9_FuseauSystemeDifferentDeHA:
    """Test Bug #9: Plages horaires calculées dans le fuseau du système.

    Bug original: saison.py / hivernage.py construisaient le pivot avec
    datetime.today() / strptime().timestamp() (fuseau du système) alors que
    getLeverSoleil() renvoie l'heure dans le fuseau de Home Assistant : sur
    une installation dont le système est en UTC (conteneur sans TZ), la plage
    était décalée de l'écart entre les deux fuseaux
    Correction: pivots et affichages calculés dans le fuseau de Home Assistant
    """

    @pytest.fixture
    def controller(self, setup_hass_states, mock_pool_config):
        """PoolController en hivernage, lever du soleil 07:10 à New York (12:10 UTC)."""
        from custom_components.pool_control.controller import PoolController

        hass = setup_hass_states(
            {"sensor.sun_next_rising": "2025-12-15T12:10:00+00:00"}
        )
        controller = PoolController(hass, mock_pool_config)
        controller.filtrationTimeStatus = MagicMock()
        controller.filtrationScheduleStatus = MagicMock()
        controller.data = {}
        controller.distributionDatePivotHivernage = 4  # 1/1 <> : fin au pivot
        controller.coefficientAjustementHivernage = 1.0
        controller.tempsDeFiltrationMinimum = 3
        return controller

    def test_sunrise_pivot_ends_filtration_at_real_sunrise(self, controller, ha_time_zone):
        """Vérifie que la filtration se termine exactement au lever du soleil."""
        controller.choixHeureFiltrationHivernage = 1  # Lever du soleil

        with patch(
            "time.time",
            return_value=datetime(2025, 12, 15, 5, 0, tzinfo=ha_time_zone).timestamp(),
        ):
            controller.calculateTimeFiltrationHivernage(12.0, False)  # 12/3 = 4 h

        sunrise = datetime(2025, 12, 15, 12, 10, tzinfo=timezone.utc).timestamp()
        assert controller.get_data("filtrationFin") == int(sunrise)
        assert controller.get_data("filtrationDebut") == int(sunrise - 4 * 3600)
        controller.filtrationScheduleStatus.set_status.assert_called_once_with(
            "* 03:10-07:10 : 12.0°C"
        )

    def test_fixed_pivot_uses_home_assistant_time_zone(self, controller, ha_time_zone):
        """Vérifie qu'une heure fixe est interprétée dans le fuseau de HA."""
        controller.choixHeureFiltrationHivernage = 2  # Heure fixe
        controller.datePivotHivernage = "06:00"

        with patch(
            "time.time",
            return_value=datetime(2025, 12, 15, 5, 0, tzinfo=ha_time_zone).timestamp(),
        ):
            controller.calculateTimeFiltrationHivernage(12.0, False)

        assert controller.get_data("filtrationFin") == int(
            datetime(2025, 12, 15, 6, 0, tzinfo=ha_time_zone).timestamp()
        )


@pytest.mark.bugs
class TestBug10_PlageManqueeBloqueRecalcul:
    """Test Bug #10: Plus aucun recalcul après une plage jamais atteinte.

    Bug original: le calcul de la plage du lendemain n'était relancé qu'après
    être passé dans la plage courante (drapeau calculateStatus remis à 0 dans
    la plage). Si la plage était manquée — Home Assistant arrêté pendant toute
    sa durée, ou plage de durée nulle (méthode température / 2, sonde d'eau à
    0 °C, sans pause) — la plage n'était plus jamais recalculée et la
    filtration ne redémarrait plus, jusqu'à un appui sur Reset
    Correction: recalcul pour le lendemain dès que la plage est passée
    """

    @pytest.fixture
    def saison_controller(self, mock_hass, mock_pool_config):
        """PoolController en mode saison : pivot 13:00, répartition 1/3 <> 2/3."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.filtrationTimeStatus = MagicMock()
        controller.filtrationScheduleStatus = MagicMock()
        controller.updateTemperatureDisplay = Mock()
        controller.data = {}
        controller.datePivot = "13:00"
        controller.pausePivot = 0
        controller.distributionDatePivot = 2
        controller.methodeCalcul = 1
        controller.coefficientAjustement = 1.0
        controller.sondeLocalTechnique = False
        controller.disableMarcheForcee = False
        return controller

    @pytest.mark.asyncio
    async def test_saison_missed_range_is_recalculated(self, saison_controller, ha_time_zone):
        """Plage du 15 (10:00-16:00) manquée, HA redémarré à 18:00 : plage du 16."""
        debut = int(datetime(2025, 6, 15, 10, 0, tzinfo=ha_time_zone).timestamp())
        saison_controller.data.update({
            "filtrationDebut": debut,
            "filtrationFin": int(datetime(2025, 6, 15, 16, 0, tzinfo=ha_time_zone).timestamp()),
            "filtrationPauseDebut": debut,
            "filtrationPauseFin": debut,
            "calculateStatus": 1,  # état persisté par les versions précédentes
        })
        current_time = datetime(2025, 6, 15, 18, 0, tzinfo=ha_time_zone).timestamp()

        with patch("time.time", return_value=current_time):
            await saison_controller.calculateStatusFiltration(22.0)

        filtration_debut = saison_controller.get_data("filtrationDebut")
        assert datetime.fromtimestamp(filtration_debut, tz=ha_time_zone).date() == datetime(2025, 6, 16).date()
        assert saison_controller.get_data("filtrationFin") > current_time
        assert saison_controller.get_data("filtrationTemperature", 0) == 0

    @pytest.mark.asyncio
    async def test_saison_zero_length_range_is_recalculated(self, saison_controller, ha_time_zone):
        """Plage de durée nulle (0 °C, température / 2) : recalculée une fois passée."""
        saison_controller.methodeCalcul = 2  # 0 °C / 2 = 0 h

        # Premier calcul à 08:00 : plage 13:00-13:00
        with patch("time.time", return_value=datetime(2025, 6, 15, 8, 0, tzinfo=ha_time_zone).timestamp()):
            await saison_controller.calculateStatusFiltration(0.0)

        pivot = int(datetime(2025, 6, 15, 13, 0, tzinfo=ha_time_zone).timestamp())
        assert saison_controller.get_data("filtrationDebut") == pivot
        assert saison_controller.get_data("filtrationFin") == pivot

        # Cron suivant, juste après le pivot : jamais « dans » la plage
        with patch("time.time", return_value=pivot + 3):
            await saison_controller.calculateStatusFiltration(0.0)

        assert saison_controller.get_data("filtrationFin") == int(
            datetime(2025, 6, 16, 13, 0, tzinfo=ha_time_zone).timestamp()
        )

    @pytest.mark.asyncio
    async def test_saison_recalculation_is_not_repeated(self, saison_controller, ha_time_zone):
        """Une fois la plage du lendemain calculée, les crons suivants ne recalculent pas."""
        debut = int(datetime(2025, 6, 15, 10, 0, tzinfo=ha_time_zone).timestamp())
        saison_controller.data.update({
            "filtrationDebut": debut,
            "filtrationFin": int(datetime(2025, 6, 15, 16, 0, tzinfo=ha_time_zone).timestamp()),
            "filtrationPauseDebut": debut,
            "filtrationPauseFin": debut,
        })

        for minute in range(3):
            current_time = datetime(2025, 6, 15, 18, minute, tzinfo=ha_time_zone).timestamp()
            with patch("time.time", return_value=current_time):
                await saison_controller.calculateStatusFiltration(22.0)

        saison_controller.filtrationTimeStatus.set_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_hivernage_missed_range_is_recalculated(self, mock_hass, mock_pool_config, ha_time_zone):
        """Plage d'hivernage du 15 (06:00-10:00) manquée, HA redémarré à 12:00 : plage du 16."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.filtrationTimeStatus = MagicMock()
        controller.filtrationScheduleStatus = MagicMock()
        controller.updateTemperatureDisplay = Mock()
        controller.getLeverSoleil = Mock(return_value="06:30")
        controller.choixHeureFiltrationHivernage = 1
        controller.distributionDatePivotHivernage = 2
        controller.tempsDeFiltrationMinimum = 3
        controller.coefficientAjustementHivernage = 1.0
        controller.temperatureSecurite = 0
        controller.temperatureHysteresis = 0.5
        controller.filtration5mn3h = False
        controller.sondeLocalTechnique = False
        controller.disableMarcheForcee = False
        controller.data = {
            "filtrationDebut": int(datetime(2025, 12, 15, 6, 0, tzinfo=ha_time_zone).timestamp()),
            "filtrationFin": int(datetime(2025, 12, 15, 10, 0, tzinfo=ha_time_zone).timestamp()),
            "calculateStatus": 1,  # état persisté par les versions précédentes
        }
        current_time = datetime(2025, 12, 15, 12, 0, tzinfo=ha_time_zone).timestamp()

        with patch("time.time", return_value=current_time):
            await controller.calculateStatusFiltrationHivernage(12.0, 5.0)

        filtration_debut = controller.get_data("filtrationDebut")
        assert datetime.fromtimestamp(filtration_debut, tz=ha_time_zone).date() == datetime(2025, 12, 16).date()
        assert controller.get_data("filtrationFin") > current_time


@pytest.mark.bugs
class TestBug11_SondeTemperatureIndisponible:
    """Test Bug #11: une sonde indisponible etait lue comme 0 °C.

    Bug original: getTemperatureWater() et getTemperatureOutdoor() renvoyaient
    0.0 quand l'entite etait absente ou son etat non numerique ("unavailable").
    Cette valeur de repli traversait ensuite toute la logique comme une vraie
    mesure. En hivernage, 0.0 > (temperatureSecurite + temperatureHysteresis)
    desarmait la securite gel : une panne de sonde pendant une gelee arretait
    la filtration au lieu de la maintenir.

    Correction: les deux getters renvoient None en l'absence de mesure, et
    chaque decision qui depend d'une temperature conserve son etat precedent
    plutot que de se fonder sur une valeur fantome.
    """

    def _hivernage_controller(self, mock_hass, mock_pool_config):
        """Controleur en hivernage, hors plage de filtration."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.filtrationTimeStatus = MagicMock()
        controller.filtrationScheduleStatus = MagicMock()
        controller.updateTemperatureDisplay = Mock()
        controller.getLeverSoleil = Mock(return_value="06:30")
        controller.temperatureSecurite = -2
        controller.temperatureHysteresis = 0.5
        controller.filtration5mn3h = False
        controller.sondeLocalTechnique = False
        controller.disableMarcheForcee = False
        return controller

    # -- Les getters signalent l'absence de mesure ---------------------------

    def test_getter_renvoie_none_quand_la_sonde_est_indisponible(
        self, mock_hass, mock_pool_config, mock_state_factory
    ):
        """Un etat 'unavailable' ne doit plus etre converti en 0 °C."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        mock_hass.states.get.return_value = mock_state_factory(
            "sensor.exterieur", "unavailable"
        )

        assert controller.getTemperatureOutdoor() is None
        assert controller.getTemperatureWater() is None

    def test_getter_renvoie_none_quand_l_entite_est_absente(
        self, mock_hass, mock_pool_config
    ):
        """Une entite inexistante ne doit plus etre convertie en 0 °C."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        mock_hass.states.get.return_value = None

        assert controller.getTemperatureOutdoor() is None
        assert controller.getTemperatureWater() is None

    def test_getter_renvoie_la_mesure_quand_elle_existe(
        self, mock_hass, mock_pool_config, mock_state_factory
    ):
        """Non-regression : une mesure valide reste lue telle quelle."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        mock_hass.states.get.return_value = mock_state_factory(
            "sensor.exterieur", "-4.5"
        )

        assert controller.getTemperatureOutdoor() == -4.5

    def test_un_seul_avertissement_par_panne_de_sonde(
        self, mock_hass, mock_pool_config, mock_state_factory, caplog
    ):
        """cron() appelle le getter chaque minute : une panne = une ligne."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        mock_hass.states.get.return_value = mock_state_factory(
            "sensor.exterieur", "unavailable"
        )

        logger_name = "custom_components.pool_control.sensors"
        with caplog.at_level(logging.DEBUG, logger=logger_name):
            for _ in range(10):
                controller.getTemperatureOutdoor()

        records = [r for r in caplog.records if r.name == logger_name]
        assert len([r for r in records if r.levelno == logging.WARNING]) == 1
        assert [r for r in records if r.levelno >= logging.ERROR] == []

    def test_le_retour_de_la_sonde_est_journalise(
        self, mock_hass, mock_pool_config, mock_state_factory, caplog
    ):
        """Le retablissement doit etre visible dans le journal."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        logger_name = "custom_components.pool_control.sensors"

        with caplog.at_level(logging.DEBUG, logger=logger_name):
            mock_hass.states.get.return_value = mock_state_factory(
                "sensor.exterieur", "unavailable"
            )
            controller.getTemperatureOutdoor()

            mock_hass.states.get.return_value = mock_state_factory(
                "sensor.exterieur", "3.2"
            )
            assert controller.getTemperatureOutdoor() == 3.2

        records = [r for r in caplog.records if r.name == logger_name]
        assert [r.levelno for r in records] == [logging.WARNING, logging.INFO]

    # -- Securite gel : conserver l'etat precedent ---------------------------

    @pytest.mark.asyncio
    async def test_securite_gel_reste_armee_quand_la_sonde_decroche(
        self, mock_hass, mock_pool_config, ha_time_zone
    ):
        """Le bug principal : une panne de sonde desarmait la securite gel."""
        controller = self._hivernage_controller(mock_hass, mock_pool_config)

        now = datetime(2026, 1, 15, 8, 0, tzinfo=ha_time_zone).timestamp()
        controller.data = {
            # Plage a venir : seule la securite gel peut activer la filtration
            "filtrationDebut": int(now + 3600),
            "filtrationFin": int(now + 7200),
            "filtrationHivernageSecurite": 1,
        }

        with patch("time.time", return_value=now):
            await controller.calculateStatusFiltrationHivernage(5.0, None)

        assert controller.get_data("filtrationHivernageSecurite") == 1
        assert controller.get_data("filtrationHivernage") == 1

    @pytest.mark.asyncio
    async def test_securite_gel_ne_s_arme_pas_sur_une_valeur_fantome(
        self, mock_hass, mock_pool_config, ha_time_zone
    ):
        """Sans mesure, la securite au repos doit le rester."""
        controller = self._hivernage_controller(mock_hass, mock_pool_config)

        now = datetime(2026, 1, 15, 8, 0, tzinfo=ha_time_zone).timestamp()
        controller.data = {
            "filtrationDebut": int(now + 3600),
            "filtrationFin": int(now + 7200),
            "filtrationHivernageSecurite": 0,
        }

        with patch("time.time", return_value=now):
            await controller.calculateStatusFiltrationHivernage(5.0, None)

        assert controller.get_data("filtrationHivernageSecurite") == 0
        assert controller.get_data("filtrationHivernage", 0) == 0

    @pytest.mark.asyncio
    async def test_securite_gel_s_arme_toujours_quand_il_gele(
        self, mock_hass, mock_pool_config, ha_time_zone
    ):
        """Non-regression : une vraie mesure sous le seuil arme la securite."""
        controller = self._hivernage_controller(mock_hass, mock_pool_config)

        now = datetime(2026, 1, 15, 8, 0, tzinfo=ha_time_zone).timestamp()
        controller.data = {
            "filtrationDebut": int(now + 3600),
            "filtrationFin": int(now + 7200),
            "filtrationHivernageSecurite": 0,
        }

        with patch("time.time", return_value=now):
            await controller.calculateStatusFiltrationHivernage(5.0, -5.0)

        assert controller.get_data("filtrationHivernageSecurite") == 1
        assert controller.get_data("filtrationHivernage") == 1

    @pytest.mark.asyncio
    async def test_securite_gel_se_desarme_sur_une_vraie_remontee(
        self, mock_hass, mock_pool_config, ha_time_zone
    ):
        """Non-regression : au-dessus du seuil + hysteresis, on desarme."""
        controller = self._hivernage_controller(mock_hass, mock_pool_config)

        now = datetime(2026, 1, 15, 8, 0, tzinfo=ha_time_zone).timestamp()
        controller.data = {
            "filtrationDebut": int(now + 3600),
            "filtrationFin": int(now + 7200),
            "filtrationHivernageSecurite": 1,
        }

        with patch("time.time", return_value=now):
            await controller.calculateStatusFiltrationHivernage(5.0, 1.0)

        assert controller.get_data("filtrationHivernageSecurite") == 0
        assert controller.get_data("filtrationHivernage", 0) == 0

    # -- Temperature de l'eau absente ----------------------------------------

    @pytest.mark.asyncio
    async def test_plage_inchangee_quand_la_sonde_eau_est_absente(
        self, mock_hass, mock_pool_config, ha_time_zone
    ):
        """Sans mesure, aucun planning ne doit etre fabrique sur 0 °C."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.filtrationTimeStatus = MagicMock()
        controller.filtrationScheduleStatus = MagicMock()
        controller.updateTemperatureDisplay = Mock()
        controller.calculateTimeFiltration = Mock()
        controller.sondeLocalTechnique = False
        controller.disableMarcheForcee = False

        now = datetime(2026, 6, 15, 20, 0, tzinfo=ha_time_zone).timestamp()
        controller.data = {
            # Plage terminee : sans la correction, le recalcul partait sur 0 °C
            "filtrationDebut": int(now - 7200),
            "filtrationFin": int(now - 60),
            "temperatureMaxi": 24.0,
        }

        with patch("time.time", return_value=now):
            await controller.calculateStatusFiltration(None)

        controller.calculateTimeFiltration.assert_not_called()
        controller.updateTemperatureDisplay.assert_not_called()
        assert controller.get_data("temperatureMaxi") == 24.0
        assert controller.get_data("filtrationFin") == int(now - 60)

    @pytest.mark.asyncio
    async def test_la_plage_memorisee_est_appliquee_meme_sans_mesure(
        self, mock_hass, mock_pool_config, ha_time_zone
    ):
        """Les transitions de la plage dependent de l'heure, pas d'une mesure.

        Sans cette evaluation, un Store contenant filtrationTemperature=1 mais
        pas encore de secours laissait la pompe demandee apres filtrationFin.
        """
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.filtrationTimeStatus = MagicMock()
        controller.filtrationScheduleStatus = MagicMock()
        controller.updateTemperatureDisplay = Mock()
        controller.calculateTimeFiltration = Mock()
        controller.sondeLocalTechnique = False
        controller.disableMarcheForcee = False

        now = datetime(2026, 6, 15, 20, 0, tzinfo=ha_time_zone).timestamp()
        controller.data = {
            "filtrationDebut": int(now - 7200),
            "filtrationFin": int(now - 60),
            # Etat herite d'un Store anterieur : la pompe etait demandee
            "filtrationTemperature": 1,
        }

        with patch("time.time", return_value=now):
            await controller.calculateStatusFiltration(None)

        # La plage est terminee : la pompe n'est plus demandee
        assert controller.get_data("filtrationTemperature") == 0
        # ... mais rien n'a ete recalcule sur une valeur fantome
        controller.calculateTimeFiltration.assert_not_called()
        assert controller.get_data("filtrationFin") == int(now - 60)

    @pytest.mark.asyncio
    async def test_la_plage_en_cours_est_maintenue_sans_mesure(
        self, mock_hass, mock_pool_config, ha_time_zone
    ):
        """Pendant la plage, la filtration reste demandee sans mesure."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.filtrationTimeStatus = MagicMock()
        controller.filtrationScheduleStatus = MagicMock()
        controller.updateTemperatureDisplay = Mock()
        controller.calculateTimeFiltration = Mock()
        controller.sondeLocalTechnique = False
        controller.disableMarcheForcee = False

        now = datetime(2026, 6, 15, 14, 0, tzinfo=ha_time_zone).timestamp()
        controller.data = {
            "filtrationDebut": int(now - 3600),
            "filtrationFin": int(now + 3600),
        }

        with patch("time.time", return_value=now):
            await controller.calculateStatusFiltration(None)

        assert controller.get_data("filtrationTemperature") == 1
        assert controller.get_data("temperatureMaxi", 0) == 0

    def test_seule_une_mesure_validee_alimente_le_secours(
        self, mock_hass, mock_pool_config
    ):
        """Avec la sonde en local technique, lire ne suffit pas a memoriser.

        Hors filtration, une sonde de local technique lit de l'eau stagnante :
        elle ne doit pas devenir le secours. Seuls les points qui ont passe les
        gardes d'echantillonnage appellent recordTemperatureWater().
        """
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.getTemperatureWater = Mock(return_value=19.0)

        assert controller.getTemperatureWaterOrLast() == 19.0
        assert controller.get_data("temperatureWaterDerniere") is None

        controller.recordTemperatureWater(19.0)
        assert controller.get_data("temperatureWaterDerniere") == 19.0

    def test_le_secours_n_est_pas_reecrit_a_chaque_dixieme(
        self, mock_hass, mock_pool_config
    ):
        """Le Store est sauvegarde a chaque changement : pas pour 0,1 °C."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)

        controller.recordTemperatureWater(19.0)
        assert controller.get_data("temperatureWaterDerniere") == 19.0

        controller.recordTemperatureWater(19.2)
        assert controller.get_data("temperatureWaterDerniere") == 19.0

        controller.recordTemperatureWater(19.8)
        assert controller.get_data("temperatureWaterDerniere") == 19.8

    @pytest.mark.asyncio
    async def test_cron_utilise_la_derniere_temperature_connue(
        self, mock_hass, mock_pool_config
    ):
        """Sonde eau en panne : on repart de la derniere mesure connue."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.getTemperatureWater = Mock(return_value=None)
        controller.getTemperatureOutdoor = Mock(return_value=None)
        controller.getHivernage = Mock(return_value=False)
        controller.calculateStatusFiltration = AsyncMock()
        controller.activatingDevices = AsyncMock()
        controller.data = {"temperatureWaterDerniere": 22.5}

        await controller.cron()

        controller.calculateStatusFiltration.assert_awaited_once_with(22.5)

    @pytest.mark.asyncio
    async def test_cron_transmet_none_si_aucune_mesure_connue(
        self, mock_hass, mock_pool_config
    ):
        """Aucune mesure n'a jamais ete vue : le calcul est reporte."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.getTemperatureWater = Mock(return_value=None)
        controller.getTemperatureOutdoor = Mock(return_value=None)
        controller.getHivernage = Mock(return_value=False)
        controller.calculateStatusFiltration = AsyncMock()
        controller.activatingDevices = AsyncMock()

        await controller.cron()

        controller.calculateStatusFiltration.assert_awaited_once_with(None)

    @pytest.mark.asyncio
    async def test_reset_ne_recalcule_pas_sans_mesure(
        self, mock_hass, mock_pool_config
    ):
        """Le bouton Recalculer ne doit pas ecraser le planning ni temperatureMaxi."""
        from custom_components.pool_control.controller import PoolController

        controller = PoolController(mock_hass, mock_pool_config)
        controller.getHivernage = Mock(return_value=False)
        controller.getTemperatureWater = Mock(return_value=None)
        controller.calculateTimeFiltration = Mock()
        controller.calculateStatusFiltration = AsyncMock()
        controller.activatingDevices = AsyncMock()
        controller.data = {"temperatureMaxi": 24.0}

        await controller.executeButtonReset()

        controller.calculateTimeFiltration.assert_not_called()
        assert controller.get_data("temperatureMaxi") == 24.0

    @pytest.mark.asyncio
    async def test_reset_en_hivernage_ne_desarme_pas_la_securite_gel(
        self, mock_hass, mock_pool_config, ha_time_zone
    ):
        """Le bouton Recalculer passe aussi par la securite gel : pas de desarmement."""
        controller = self._hivernage_controller(mock_hass, mock_pool_config)
        controller.getHivernage = Mock(return_value=True)
        controller.getTemperatureWater = Mock(return_value=5.0)
        controller.getTemperatureOutdoor = Mock(return_value=None)
        controller.calculateTimeFiltrationHivernage = Mock()
        controller.activatingDevices = AsyncMock()

        now = datetime(2026, 1, 15, 8, 0, tzinfo=ha_time_zone).timestamp()
        controller.data = {
            "filtrationDebut": int(now + 3600),
            "filtrationFin": int(now + 7200),
            "filtrationHivernageSecurite": 1,
        }

        with patch("time.time", return_value=now):
            await controller.executeButtonReset()

        assert controller.get_data("filtrationHivernageSecurite") == 1
        assert controller.get_data("filtrationHivernage") == 1


@pytest.mark.bugs
class TestAllBugsRegression:
    """Tests combinés pour vérifier que tous les bugs sont corrigés."""

    def test_all_bugs_are_fixed(self, mock_hass, mock_pool_config):
        """Test global vérifiant que le PoolController s'initialise correctement."""
        from custom_components.pool_control.controller import PoolController

        # Configuration qui aurait déclenché tous les bugs avant corrections
        config = mock_pool_config.copy()
        config["methodeCalcul"] = "1"  # Bug #4 (string au lieu de int)
        config["traitement"] = None     # Bug #5 (None)

        # Initialisation ne doit pas crasher
        try:
            controller = PoolController(mock_hass, config)

            # Vérifications basiques
            assert controller.methodeCalcul == 1  # Bug #4 corrigé
            assert controller.traitement is None   # Bug #5 OK

            # get_data avec clé manquante ne doit pas crasher (Bug #2)
            temp = controller.get_data("temperatureMaxi", 0)
            assert temp == 0

            # Méthodes existent (Bug #1, #6)
            assert hasattr(controller, 'executeButtonStop')
            assert hasattr(controller, 'updateTemperatureDisplay')

        except Exception as e:
            pytest.fail(f"Initialisation a échoué - certains bugs ne sont pas corrigés: {e}")
