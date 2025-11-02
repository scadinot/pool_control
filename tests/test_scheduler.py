"""Tests for scheduler.py module - Cron scheduling and periodic tasks.

Tests the scheduler methods that manage periodic task execution for pool automation.
The module handles two main cron jobs:
- 5-second cron for monitoring surpresseur and filter washing timers
- 1-minute cron for filtration status calculation and device refresh

Functions tested:
1. __init__() - Initialize scheduler with default values
2. startSecondCron() - Start 5-second interval cron
3. stopSecondCron() - Stop 5-second interval cron
4. pull(now=None) - 5-second routine for timer monitoring
5. startFirstCron() - Start 1-minute interval cron
6. cron(now=None) - 1-minute routine for pool automation
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import timedelta
import time

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")


@pytest.fixture
def mock_scheduler_controller(mock_hass, mock_pool_config):
    """Create a mock controller with SchedulerMixin."""
    from custom_components.pool_control.controller import PoolController

    controller = PoolController(mock_hass, mock_pool_config)

    # Mock scheduler dependencies
    controller.surpresseurStatus = MagicMock()
    controller.filtreSableLavageStatus = MagicMock()
    controller.traitement = "switch.traitement"
    controller.traitement_2 = "switch.traitement_2"

    # Mock methods called by cron
    controller.getTemperatureWater = Mock(return_value=25.0)
    controller.getTemperatureOutdoor = Mock(return_value=22.0)
    controller.refreshFiltration = AsyncMock()
    controller.refreshSurpresseur = AsyncMock()
    controller.refreshTraitement = AsyncMock()
    controller.refreshTraitement_2 = AsyncMock()
    controller.getHivernage = Mock(return_value=False)
    controller.calculateStatusFiltration = AsyncMock()
    controller.calculateStatusFiltrationHivernage = AsyncMock()
    controller.activatingDevices = AsyncMock()
    controller.executeButtonStop = AsyncMock()
    controller.executeFiltreSableLavageOn = AsyncMock()

    return controller


@pytest.mark.unit
class TestSchedulerInit:
    """Tests for __init__() - Scheduler initialization."""

    def test_initializes_second_cron_cancel(self, mock_scheduler_controller):
        """Test __init__ sets secondCronCancel to None."""
        assert mock_scheduler_controller.secondCronCancel is None

    def test_initializes_filtration_refresh_counter(self, mock_scheduler_controller):
        """Test __init__ sets filtrationRefreshCounter to 0."""
        assert mock_scheduler_controller.filtrationRefreshCounter == 0


@pytest.mark.unit
class TestStartSecondCron:
    """Tests for startSecondCron() - Start 5-second interval cron."""

    @pytest.mark.asyncio
    async def test_registers_interval_callback(self, mock_scheduler_controller):
        """Test startSecondCron registers a 5-second interval callback."""
        mock_cancel = Mock()

        with patch(
            "custom_components.pool_control.scheduler.async_track_time_interval",
            return_value=mock_cancel,
        ) as mock_track:
            await mock_scheduler_controller.startSecondCron()

            # Verify async_track_time_interval was called correctly
            mock_track.assert_called_once_with(
                mock_scheduler_controller.hass,
                mock_scheduler_controller.pull,
                timedelta(seconds=5),
            )

            # Verify cancel function was stored
            assert mock_scheduler_controller.secondCronCancel == mock_cancel

    @pytest.mark.asyncio
    async def test_cancels_existing_cron_before_starting(self, mock_scheduler_controller):
        """Test startSecondCron cancels existing cron before starting new one."""
        existing_cancel = Mock()
        mock_scheduler_controller.secondCronCancel = existing_cancel

        with patch(
            "custom_components.pool_control.scheduler.async_track_time_interval",
            return_value=Mock(),
        ):
            await mock_scheduler_controller.startSecondCron()

            # Verify old cron was cancelled
            existing_cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_no_existing_cron(self, mock_scheduler_controller):
        """Test startSecondCron works when no existing cron is running."""
        mock_scheduler_controller.secondCronCancel = None

        with patch(
            "custom_components.pool_control.scheduler.async_track_time_interval",
            return_value=Mock(),
        ):
            # Should not crash
            await mock_scheduler_controller.startSecondCron()


@pytest.mark.unit
class TestStopSecondCron:
    """Tests for stopSecondCron() - Stop 5-second interval cron."""

    @pytest.mark.asyncio
    async def test_cancels_running_cron(self, mock_scheduler_controller):
        """Test stopSecondCron cancels the running cron job."""
        mock_cancel = Mock()
        mock_scheduler_controller.secondCronCancel = mock_cancel

        await mock_scheduler_controller.stopSecondCron()

        # Verify cancel was called
        mock_cancel.assert_called_once()
        # Verify secondCronCancel is set to None
        assert mock_scheduler_controller.secondCronCancel is None

    @pytest.mark.asyncio
    async def test_handles_no_running_cron(self, mock_scheduler_controller):
        """Test stopSecondCron handles case when no cron is running."""
        mock_scheduler_controller.secondCronCancel = None

        # Should not crash
        await mock_scheduler_controller.stopSecondCron()

        assert mock_scheduler_controller.secondCronCancel is None


@pytest.mark.unit
class TestPull:
    """Tests for pull() - 5-second routine for timer monitoring."""

    @pytest.mark.asyncio
    async def test_updates_surpresseur_timer_display(self, mock_scheduler_controller):
        """Test pull updates surpresseur status display when timer is active."""
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 1,  # Active
                "filtrationTempsRestant": 1300,  # 300 seconds remaining (from epoch)
                "filtrationLavageEtat": 0,
            }.get(key, default)
        )

        with patch("time.time", return_value=1000.0):
            await mock_scheduler_controller.pull()

        # Status should be updated with "Actif : MM:SS"
        mock_scheduler_controller.surpresseurStatus.set_status.assert_called_once()
        call_arg = (
            mock_scheduler_controller.surpresseurStatus.set_status.call_args[0][0]
        )
        assert call_arg.startswith("Actif : ")

    @pytest.mark.asyncio
    async def test_calls_stop_when_surpresseur_timer_expires(
        self, mock_scheduler_controller
    ):
        """Test pull calls executeButtonStop when surpresseur timer expires."""
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 1,  # Active
                "filtrationTempsRestant": 500,  # Timer expired (500 < 1000)
                "filtrationLavageEtat": 0,
            }.get(key, default)
        )

        with patch("time.time", return_value=1000.0):
            await mock_scheduler_controller.pull()

        # Should call stop when timer expires
        mock_scheduler_controller.executeButtonStop.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_lavage_timer_display(self, mock_scheduler_controller):
        """Test pull updates lavage status display during washing (state 2)."""
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 0,
                "filtrationLavageEtat": 2,  # Lavage state
                "filtrationTempsRestant": 1180,  # 180 seconds remaining
            }.get(key, default)
        )

        with patch("time.time", return_value=1000.0):
            await mock_scheduler_controller.pull()

        # Status should be updated with "Lavage : MM:SS"
        mock_scheduler_controller.filtreSableLavageStatus.set_status.assert_called_once()
        call_arg = (
            mock_scheduler_controller.filtreSableLavageStatus.set_status.call_args[0][0]
        )
        assert call_arg.startswith("Lavage : ")

    @pytest.mark.asyncio
    async def test_updates_rincage_timer_display(self, mock_scheduler_controller):
        """Test pull updates lavage status display during rinsing (state 4)."""
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 0,
                "filtrationLavageEtat": 4,  # Rinçage state
                "filtrationTempsRestant": 1120,  # 120 seconds remaining
            }.get(key, default)
        )

        with patch("time.time", return_value=1000.0):
            await mock_scheduler_controller.pull()

        # Status should be updated with "Rinçage : MM:SS"
        call_arg = (
            mock_scheduler_controller.filtreSableLavageStatus.set_status.call_args[0][0]
        )
        assert call_arg.startswith("Rinçage : ")

    @pytest.mark.asyncio
    async def test_calls_lavage_on_when_timer_expires(self, mock_scheduler_controller):
        """Test pull calls executeFiltreSableLavageOn when lavage timer expires."""
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 0,
                "filtrationLavageEtat": 2,  # Lavage state
                "filtrationTempsRestant": 500,  # Timer expired (500 < 1000)
            }.get(key, default)
        )

        with patch("time.time", return_value=1000.0):
            await mock_scheduler_controller.pull()

        # Should advance lavage state machine
        mock_scheduler_controller.executeFiltreSableLavageOn.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_surpresseur_inactive(self, mock_scheduler_controller):
        """Test pull skips surpresseur updates when inactive."""
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 0,  # Inactive
                "filtrationLavageEtat": 0,
            }.get(key, default)
        )

        await mock_scheduler_controller.pull()

        # Should not update status
        mock_scheduler_controller.surpresseurStatus.set_status.assert_not_called()
        mock_scheduler_controller.executeButtonStop.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_lavage_not_in_timed_state(
        self, mock_scheduler_controller
    ):
        """Test pull skips lavage updates when not in state 2 or 4."""
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 0,
                "filtrationLavageEtat": 1,  # Not timed state (only 2 and 4 are timed)
            }.get(key, default)
        )

        await mock_scheduler_controller.pull()

        # Should not update lavage status
        mock_scheduler_controller.filtreSableLavageStatus.set_status.assert_not_called()
        mock_scheduler_controller.executeFiltreSableLavageOn.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_no_status_objects(self, mock_scheduler_controller):
        """Test pull handles missing status objects gracefully."""
        mock_scheduler_controller.surpresseurStatus = None
        mock_scheduler_controller.filtreSableLavageStatus = None
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 1,
                "filtrationTempsRestant": 1300,
                "filtrationLavageEtat": 2,
            }.get(key, default)
        )

        with patch("time.time", return_value=1000.0):
            # Should not crash
            await mock_scheduler_controller.pull()


@pytest.mark.unit
class TestStartFirstCron:
    """Tests for startFirstCron() - Start 1-minute interval cron."""

    @pytest.mark.asyncio
    async def test_registers_minute_interval_callback(self, mock_scheduler_controller):
        """Test startFirstCron registers a 1-minute interval callback."""
        with patch(
            "custom_components.pool_control.scheduler.async_track_time_interval"
        ) as mock_track:
            await mock_scheduler_controller.startFirstCron()

            # Verify async_track_time_interval was called correctly
            mock_track.assert_called_once_with(
                mock_scheduler_controller.hass,
                mock_scheduler_controller.cron,
                timedelta(minutes=1),
            )


@pytest.mark.unit
class TestCron:
    """Tests for cron() - 1-minute routine for pool automation."""

    @pytest.mark.asyncio
    async def test_calls_refresh_every_5_minutes(self, mock_scheduler_controller):
        """Test cron calls refresh functions when counter reaches 5."""
        mock_scheduler_controller.filtrationRefreshCounter = 5

        await mock_scheduler_controller.cron()

        # All refresh functions should be called
        mock_scheduler_controller.refreshFiltration.assert_called_once()
        mock_scheduler_controller.refreshSurpresseur.assert_called_once()
        mock_scheduler_controller.refreshTraitement.assert_called_once()
        mock_scheduler_controller.refreshTraitement_2.assert_called_once()

        # Counter should be reset
        assert mock_scheduler_controller.filtrationRefreshCounter == 0

    @pytest.mark.asyncio
    async def test_increments_counter_when_not_time_to_refresh(
        self, mock_scheduler_controller
    ):
        """Test cron increments counter when not time to refresh."""
        mock_scheduler_controller.filtrationRefreshCounter = 2

        await mock_scheduler_controller.cron()

        # Refresh should not be called
        mock_scheduler_controller.refreshFiltration.assert_not_called()
        # Counter should be incremented
        assert mock_scheduler_controller.filtrationRefreshCounter == 3

    @pytest.mark.asyncio
    async def test_skips_traitement_when_not_configured(
        self, mock_scheduler_controller
    ):
        """Test cron skips treatment refresh when not configured."""
        mock_scheduler_controller.filtrationRefreshCounter = 5
        mock_scheduler_controller.traitement = None
        mock_scheduler_controller.traitement_2 = None

        await mock_scheduler_controller.cron()

        # Should not call treatment refresh
        mock_scheduler_controller.refreshTraitement.assert_not_called()
        mock_scheduler_controller.refreshTraitement_2.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_hivernage_calculation_when_active(
        self, mock_scheduler_controller
    ):
        """Test cron calls hivernage calculation when winterization is active."""
        mock_scheduler_controller.getHivernage = Mock(return_value=True)

        await mock_scheduler_controller.cron()

        # Should call hivernage calculation
        mock_scheduler_controller.calculateStatusFiltrationHivernage.assert_called_once_with(
            25.0, 22.0  # Water and outdoor temps
        )
        # Should not call normal filtration calculation
        mock_scheduler_controller.calculateStatusFiltration.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_normal_calculation_when_no_hivernage(
        self, mock_scheduler_controller
    ):
        """Test cron calls normal filtration calculation when winterization is inactive."""
        mock_scheduler_controller.getHivernage = Mock(return_value=False)

        await mock_scheduler_controller.cron()

        # Should call normal filtration calculation
        mock_scheduler_controller.calculateStatusFiltration.assert_called_once_with(
            25.0  # Water temp
        )
        # Should not call hivernage calculation
        mock_scheduler_controller.calculateStatusFiltrationHivernage.assert_not_called()

    @pytest.mark.asyncio
    async def test_always_calls_activating_devices(self, mock_scheduler_controller):
        """Test cron always calls activatingDevices at the end."""
        await mock_scheduler_controller.cron()

        # Should always call activatingDevices
        mock_scheduler_controller.activatingDevices.assert_called_once()

    @pytest.mark.asyncio
    async def test_gets_temperatures_every_minute(self, mock_scheduler_controller):
        """Test cron gets temperatures every minute."""
        await mock_scheduler_controller.cron()

        # Should get both temperatures
        mock_scheduler_controller.getTemperatureWater.assert_called_once()
        mock_scheduler_controller.getTemperatureOutdoor.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_counter_cycles_correctly(self, mock_scheduler_controller):
        """Test refresh counter cycles from 0 to 5 and resets."""
        # Start at 0
        mock_scheduler_controller.filtrationRefreshCounter = 0

        # Call cron 5 times
        for i in range(5):
            await mock_scheduler_controller.cron()
            assert mock_scheduler_controller.filtrationRefreshCounter == i + 1

        # On 6th call (counter = 5), should refresh and reset to 0
        await mock_scheduler_controller.cron()
        assert mock_scheduler_controller.filtrationRefreshCounter == 0
        mock_scheduler_controller.refreshFiltration.assert_called_once()


@pytest.mark.integration
class TestSchedulerIntegration:
    """Integration tests for scheduler functionality."""

    @pytest.mark.asyncio
    async def test_start_stop_cycle(self, mock_scheduler_controller):
        """Test starting and stopping second cron."""
        mock_cancel = Mock()

        with patch(
            "custom_components.pool_control.scheduler.async_track_time_interval",
            return_value=mock_cancel,
        ):
            # Start cron
            await mock_scheduler_controller.startSecondCron()
            assert mock_scheduler_controller.secondCronCancel is not None

            # Stop cron
            await mock_scheduler_controller.stopSecondCron()
            assert mock_scheduler_controller.secondCronCancel is None
            mock_cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_pull_handles_both_timers_active(self, mock_scheduler_controller):
        """Test pull handles both surpresseur and lavage timers active simultaneously."""
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 1,
                "filtrationLavageEtat": 2,
                "filtrationTempsRestant": 1300,
            }.get(key, default)
        )

        with patch("time.time", return_value=1000.0):
            await mock_scheduler_controller.pull()

        # Both status displays should be updated
        mock_scheduler_controller.surpresseurStatus.set_status.assert_called_once()
        mock_scheduler_controller.filtreSableLavageStatus.set_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_cron_full_5minute_cycle(self, mock_scheduler_controller):
        """Test complete 5-minute refresh cycle."""
        mock_scheduler_controller.filtrationRefreshCounter = 0

        # Run 4 cron cycles - no refresh yet
        for _ in range(4):
            await mock_scheduler_controller.cron()
            mock_scheduler_controller.refreshFiltration.assert_not_called()

        # 5th cycle should trigger refresh
        await mock_scheduler_controller.cron()
        mock_scheduler_controller.refreshFiltration.assert_called_once()

        # Next cycle should start counting again
        await mock_scheduler_controller.cron()
        assert mock_scheduler_controller.filtrationRefreshCounter == 1

    @pytest.mark.asyncio
    async def test_timer_expiration_sequence(self, mock_scheduler_controller):
        """Test timer expiration triggers correct actions."""
        # Timer active but not expired
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 1,
                "filtrationTempsRestant": 2000,
                "filtrationLavageEtat": 0,
            }.get(key, default)
        )

        with patch("time.time", return_value=1000.0):
            await mock_scheduler_controller.pull()
            mock_scheduler_controller.executeButtonStop.assert_not_called()

        # Timer expired
        mock_scheduler_controller.get_data = Mock(
            side_effect=lambda key, default: {
                "filtrationSurpresseur": 1,
                "filtrationTempsRestant": 500,  # Expired
                "filtrationLavageEtat": 0,
            }.get(key, default)
        )

        with patch("time.time", return_value=1000.0):
            await mock_scheduler_controller.pull()
            mock_scheduler_controller.executeButtonStop.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_treatment_configuration(self, mock_scheduler_controller):
        """Test cron works with only one treatment configured."""
        mock_scheduler_controller.filtrationRefreshCounter = 5
        mock_scheduler_controller.traitement = "switch.traitement"
        mock_scheduler_controller.traitement_2 = None  # Only one configured

        await mock_scheduler_controller.cron()

        # Should call refresh for traitement but not traitement_2
        mock_scheduler_controller.refreshTraitement.assert_called_once()
        mock_scheduler_controller.refreshTraitement_2.assert_not_called()
