"""Tests for lavage.py module - Filter washing state machine.

Tests the lavage (filter cleaning) state machine that manages the automatic
sand filter cleaning process through multiple states.

State Machine:
- State 0: Stopped → State 1 (Stop, washing position)
- State 1: Washing position → State 2 (Washing) or State 4 (if rinse = 0)
- State 2: Washing → State 3 (Stop, rinse position)
- State 3: Rinse position → State 4 (Rinsing)
- State 4: Rinsing → State 5 (Stop, filtration position)
- State 5: Filtration position → State 0 (Stopped)

Functions tested:
1. executeFiltreSableLavageOn() - Main state machine function
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import time
from datetime import datetime

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")


@pytest.fixture
def mock_lavage_controller(mock_hass, mock_pool_config):
    """Create a mock controller with LavageMixin."""
    from custom_components.pool_control.controller import PoolController

    controller = PoolController(mock_hass, mock_pool_config)

    # Mock methods
    controller.activatingDevices = AsyncMock()
    controller.startSecondCron = AsyncMock()
    controller.stopSecondCron = AsyncMock()

    # Mock filtreSableLavageStatus
    controller.filtreSableLavageStatus = MagicMock()
    controller.filtreSableLavageStatus.set_status = Mock()

    # Initialize data dict
    controller.data = {}

    # Set default config values
    controller.lavageDuree = 5  # 5 minutes
    controller.rincageDuree = 2  # 2 minutes

    return controller


@pytest.mark.unit
class TestLavageStateTransitions:
    """Tests for lavage state machine transitions."""

    @pytest.mark.asyncio
    async def test_state_0_to_1_transition(self, mock_lavage_controller):
        """Test transition from state 0 (Stopped) to state 1 (Washing position)."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 0

        await mock_lavage_controller.executeFiltreSableLavageOn()

        # Should transition to state 1
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 1
        assert mock_lavage_controller.get_data("filtrationLavage") == 1
        mock_lavage_controller.filtreSableLavageStatus.set_status.assert_called_once_with(
            "Arrêt, position lavage"
        )
        mock_lavage_controller.activatingDevices.assert_called_once()
        mock_lavage_controller.startSecondCron.assert_called_once()

    @pytest.mark.asyncio
    async def test_state_1_to_2_transition(self, mock_lavage_controller):
        """Test transition from state 1 to state 2 (Washing in progress)."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 1
        mock_lavage_controller.lavageDuree = 5

        with patch('time.time', return_value=1000.0):
            await mock_lavage_controller.executeFiltreSableLavageOn()

        # Should transition to state 2
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 2
        assert mock_lavage_controller.get_data("filtrationLavage") == 2
        # Time should be set to now + 5 minutes (300 seconds)
        assert mock_lavage_controller.get_data("filtrationTempsRestant") == 1300
        mock_lavage_controller.activatingDevices.assert_called_once()

    @pytest.mark.asyncio
    async def test_state_1_skip_to_4_when_rinse_zero(self, mock_lavage_controller):
        """Test state 1 skips to state 4 when rinse duration is 0."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 1
        mock_lavage_controller.rincageDuree = 0  # No rinse

        await mock_lavage_controller.executeFiltreSableLavageOn()

        # Should skip directly to state 4
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 4

    @pytest.mark.asyncio
    async def test_state_2_to_3_transition(self, mock_lavage_controller):
        """Test transition from state 2 to state 3 (Rinse position)."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 2

        await mock_lavage_controller.executeFiltreSableLavageOn()

        # Should transition to state 3
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 3
        assert mock_lavage_controller.get_data("filtrationLavage") == 1
        mock_lavage_controller.filtreSableLavageStatus.set_status.assert_called_once_with(
            "Arrêt, position rinçage"
        )
        mock_lavage_controller.activatingDevices.assert_called_once()

    @pytest.mark.asyncio
    async def test_state_3_to_4_transition(self, mock_lavage_controller):
        """Test transition from state 3 to state 4 (Rinsing in progress)."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 3
        mock_lavage_controller.rincageDuree = 2

        with patch('time.time', return_value=2000.0):
            await mock_lavage_controller.executeFiltreSableLavageOn()

        # Should transition to state 4
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 4
        assert mock_lavage_controller.get_data("filtrationLavage") == 2
        # Time should be set to now + 2 minutes (120 seconds)
        assert mock_lavage_controller.get_data("filtrationTempsRestant") == 2120
        mock_lavage_controller.activatingDevices.assert_called_once()

    @pytest.mark.asyncio
    async def test_state_4_to_5_transition(self, mock_lavage_controller):
        """Test transition from state 4 to state 5 (Filtration position)."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 4

        await mock_lavage_controller.executeFiltreSableLavageOn()

        # Should transition to state 5
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 5
        assert mock_lavage_controller.get_data("filtrationLavage") == 1
        mock_lavage_controller.filtreSableLavageStatus.set_status.assert_called_once_with(
            "Arrêt, position filtration"
        )
        mock_lavage_controller.activatingDevices.assert_called_once()

    @pytest.mark.asyncio
    async def test_state_5_to_0_transition(self, mock_lavage_controller):
        """Test transition from state 5 to state 0 (Stopped - cycle complete)."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 5

        await mock_lavage_controller.executeFiltreSableLavageOn()

        # Should transition back to state 0
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 0
        assert mock_lavage_controller.get_data("filtrationLavage") == 0
        mock_lavage_controller.filtreSableLavageStatus.set_status.assert_called_once_with(
            "Arrêté"
        )
        mock_lavage_controller.activatingDevices.assert_called_once()
        mock_lavage_controller.stopSecondCron.assert_called_once()


@pytest.mark.unit
class TestLavageStatusDisplay:
    """Tests for lavage status display formatting."""

    @pytest.mark.asyncio
    async def test_washing_status_display_format(self, mock_lavage_controller):
        """Test washing status display shows correct format."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 1
        mock_lavage_controller.lavageDuree = 5

        with patch('time.time', return_value=1000.0):
            await mock_lavage_controller.executeFiltreSableLavageOn()

        # Status should show "Lavage : MM:SS"
        call_args = mock_lavage_controller.filtreSableLavageStatus.set_status.call_args[0][0]
        assert call_args.startswith("Lavage : ")
        assert ":" in call_args.split(" : ")[1]  # Time format

    @pytest.mark.asyncio
    async def test_rinsing_status_display_format(self, mock_lavage_controller):
        """Test rinsing status display shows correct format."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 3
        mock_lavage_controller.rincageDuree = 2

        with patch('time.time', return_value=2000.0):
            await mock_lavage_controller.executeFiltreSableLavageOn()

        # Status should show "Rinçage : MM:SS"
        call_args = mock_lavage_controller.filtreSableLavageStatus.set_status.call_args[0][0]
        assert call_args.startswith("Rinçage : ")
        assert ":" in call_args.split(" : ")[1]  # Time format

    @pytest.mark.asyncio
    async def test_status_not_updated_without_status_object(self, mock_lavage_controller):
        """Test that missing status object doesn't crash."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 0
        mock_lavage_controller.filtreSableLavageStatus = None

        # Should not crash
        await mock_lavage_controller.executeFiltreSableLavageOn()

        # State transition should still work
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 1


@pytest.mark.unit
class TestLavageTimeCalculation:
    """Tests for lavage time calculation."""

    @pytest.mark.asyncio
    async def test_washing_time_calculation(self, mock_lavage_controller):
        """Test washing time is correctly calculated."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 1
        mock_lavage_controller.lavageDuree = 10  # 10 minutes

        current_time = 5000.0
        with patch('time.time', return_value=current_time):
            await mock_lavage_controller.executeFiltreSableLavageOn()

        expected_end_time = int(current_time + (10 * 60))  # 5000 + 600 = 5600
        assert mock_lavage_controller.get_data("filtrationTempsRestant") == expected_end_time

    @pytest.mark.asyncio
    async def test_rinsing_time_calculation(self, mock_lavage_controller):
        """Test rinsing time is correctly calculated."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 3
        mock_lavage_controller.rincageDuree = 3  # 3 minutes

        current_time = 7000.0
        with patch('time.time', return_value=current_time):
            await mock_lavage_controller.executeFiltreSableLavageOn()

        expected_end_time = int(current_time + (3 * 60))  # 7000 + 180 = 7180
        assert mock_lavage_controller.get_data("filtrationTempsRestant") == expected_end_time

    @pytest.mark.asyncio
    async def test_time_display_accuracy(self, mock_lavage_controller):
        """Test time display shows minutes and seconds correctly."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 1
        mock_lavage_controller.lavageDuree = 5  # 5 minutes = 300 seconds

        with patch('time.time', return_value=1000.0):
            await mock_lavage_controller.executeFiltreSableLavageOn()

        # Status should show 05:00
        call_args = mock_lavage_controller.filtreSableLavageStatus.set_status.call_args[0][0]
        time_part = call_args.split(" : ")[1]
        assert time_part == "05:00"


@pytest.mark.unit
class TestLavageFiltrationLavageValues:
    """Tests for filtrationLavage values."""

    @pytest.mark.asyncio
    async def test_filtration_lavage_stop_states(self, mock_lavage_controller):
        """Test filtrationLavage is 1 (stop) during position changes."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0

        # Test state 0 -> 1 (position lavage)
        mock_lavage_controller.data["filtrationLavageEtat"] = 0
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavage") == 1

        # Test state 2 -> 3 (position rinçage)
        mock_lavage_controller.data["filtrationLavageEtat"] = 2
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavage") == 1

        # Test state 4 -> 5 (position filtration)
        mock_lavage_controller.data["filtrationLavageEtat"] = 4
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavage") == 1

    @pytest.mark.asyncio
    async def test_filtration_lavage_running_states(self, mock_lavage_controller):
        """Test filtrationLavage is 2 (running) during washing/rinsing."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0

        # Test state 1 -> 2 (washing)
        mock_lavage_controller.data["filtrationLavageEtat"] = 1
        with patch('time.time', return_value=1000.0):
            await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavage") == 2

        # Test state 3 -> 4 (rinsing)
        mock_lavage_controller.data["filtrationLavageEtat"] = 3
        with patch('time.time', return_value=2000.0):
            await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavage") == 2

    @pytest.mark.asyncio
    async def test_filtration_lavage_stopped_state(self, mock_lavage_controller):
        """Test filtrationLavage is 0 (normal) when cycle complete."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 5

        await mock_lavage_controller.executeFiltreSableLavageOn()

        assert mock_lavage_controller.get_data("filtrationLavage") == 0


@pytest.mark.unit
class TestLavageSupresseurBlocking:
    """Tests for surpresseur blocking lavage."""

    @pytest.mark.asyncio
    async def test_lavage_blocked_when_surpresseur_active(self, mock_lavage_controller):
        """Test lavage doesn't execute when surpresseur is active."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 1  # Active
        mock_lavage_controller.data["filtrationLavageEtat"] = 0

        await mock_lavage_controller.executeFiltreSableLavageOn()

        # State should not change
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 0
        mock_lavage_controller.activatingDevices.assert_not_called()

    @pytest.mark.asyncio
    async def test_lavage_executes_when_surpresseur_inactive(self, mock_lavage_controller):
        """Test lavage executes normally when surpresseur is inactive."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0  # Inactive
        mock_lavage_controller.data["filtrationLavageEtat"] = 0

        await mock_lavage_controller.executeFiltreSableLavageOn()

        # State should change
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 1
        mock_lavage_controller.activatingDevices.assert_called_once()


@pytest.mark.integration
class TestLavageFullCycle:
    """Integration tests for complete lavage cycle."""

    @pytest.mark.asyncio
    async def test_full_lavage_cycle_with_rinse(self, mock_lavage_controller):
        """Test complete lavage cycle from start to finish with rinse."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 0
        mock_lavage_controller.lavageDuree = 5
        mock_lavage_controller.rincageDuree = 2

        current_time = 1000.0

        # State 0 -> 1
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 1

        # State 1 -> 2
        with patch('time.time', return_value=current_time):
            await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 2

        # State 2 -> 3
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 3

        # State 3 -> 4
        with patch('time.time', return_value=current_time + 500):
            await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 4

        # State 4 -> 5
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 5

        # State 5 -> 0 (complete)
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 0

        # Verify cron was started and stopped
        mock_lavage_controller.startSecondCron.assert_called_once()
        mock_lavage_controller.stopSecondCron.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_lavage_cycle_without_rinse(self, mock_lavage_controller):
        """Test complete lavage cycle skipping rinse when duration is 0."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 0
        mock_lavage_controller.lavageDuree = 5
        mock_lavage_controller.rincageDuree = 0  # Skip rinse

        # State 0 -> 1
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 1

        # State 1 -> 4 (skips 2 and 3)
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 4

        # State 4 -> 5
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 5

        # State 5 -> 0
        await mock_lavage_controller.executeFiltreSableLavageOn()
        assert mock_lavage_controller.get_data("filtrationLavageEtat") == 0

    @pytest.mark.asyncio
    async def test_activating_devices_called_at_every_step(self, mock_lavage_controller):
        """Test activatingDevices is called at every state transition."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 0
        mock_lavage_controller.rincageDuree = 0  # Simplify

        transitions = [0, 1, 4, 5]
        for _ in transitions:
            await mock_lavage_controller.executeFiltreSableLavageOn()

        # Should be called 4 times (once per transition)
        assert mock_lavage_controller.activatingDevices.call_count == 4

    @pytest.mark.asyncio
    async def test_status_updates_throughout_cycle(self, mock_lavage_controller):
        """Test status is updated correctly throughout the cycle."""
        mock_lavage_controller.data["filtrationSurpresseur"] = 0
        mock_lavage_controller.data["filtrationLavageEtat"] = 0
        mock_lavage_controller.lavageDuree = 5
        mock_lavage_controller.rincageDuree = 2

        status_calls = []

        def capture_status(status):
            status_calls.append(status)

        mock_lavage_controller.filtreSableLavageStatus.set_status.side_effect = capture_status

        # Go through all states
        await mock_lavage_controller.executeFiltreSableLavageOn()  # 0 -> 1
        with patch('time.time', return_value=1000.0):
            await mock_lavage_controller.executeFiltreSableLavageOn()  # 1 -> 2
        await mock_lavage_controller.executeFiltreSableLavageOn()  # 2 -> 3
        with patch('time.time', return_value=2000.0):
            await mock_lavage_controller.executeFiltreSableLavageOn()  # 3 -> 4
        await mock_lavage_controller.executeFiltreSableLavageOn()  # 4 -> 5
        await mock_lavage_controller.executeFiltreSableLavageOn()  # 5 -> 0

        # Verify status sequence
        assert "Arrêt, position lavage" in status_calls
        assert any("Lavage :" in s for s in status_calls)
        assert "Arrêt, position rinçage" in status_calls
        assert any("Rinçage :" in s for s in status_calls)
        assert "Arrêt, position filtration" in status_calls
        assert "Arrêté" in status_calls
