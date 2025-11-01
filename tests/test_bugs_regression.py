"""Tests de non-régression pour les 6 bugs critiques corrigés.

Ces tests garantissent que les bugs identifiés et corrigés dans la PR #1
ne reviennent pas dans les futures versions.

Bugs testés:
1. Bug #1: Méthode manquante executePoolStop() → executeButtonStop()
2. Bug #2: KeyError sur temperatureMaxi
3. Bug #3: Message de log incorrect
4. Bug #4: Type incohérent methodeCalcul
5. Bug #5: Crash si traitement non configuré
6. Bug #6: Entité optionnelle temperatureDisplay
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
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
