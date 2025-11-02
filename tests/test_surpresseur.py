"""Tests for surpresseur.py module - Booster pump control.

Tests the booster pump control methods that manage the pool's booster pump device.
The surpresseur is used to increase water pressure for various pool operations.

Functions tested:
1. executeSurpresseurOn() - Start booster pump with timer
2. refreshSurpresseur() - Refresh booster pump state
3. getStateSurpresseur() - Get booster pump state (bool)
4. surpresseurOn(repeat=False) - Turn on booster pump
5. surpresseurStop(repeat=False) - Turn off booster pump
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import time

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")


@pytest.fixture
def mock_surpresseur_controller(mock_hass, mock_pool_config):
    """Create a mock controller with SurpresseurMixin."""
    from custom_components.pool_control.controller import PoolController

    controller = PoolController(mock_hass, mock_pool_config)

    # Mock surpresseur configuration
    controller.surpresseur = "switch.surpresseur"
    controller.surpresseurDuree = 10  # 10 minutes
    controller.surpresseurStatus = MagicMock()

    # Mock required methods
    controller.activatingDevices = AsyncMock()
    controller.startSecondCron = AsyncMock()
    controller.stopSecondCron = AsyncMock()

    return controller


@pytest.mark.unit
class TestExecuteSurpresseurOn:
    """Tests for executeSurpresseurOn() - Start booster pump with timer."""

    @pytest.mark.asyncio
    async def test_starts_surpresseur_when_idle(self, mock_surpresseur_controller):
        """Test executeSurpresseurOn starts when system is idle."""
        mock_surpresseur_controller.get_data = Mock(return_value=0)
        mock_surpresseur_controller.set_data = Mock()

        with patch('time.time', return_value=1000.0):
            await mock_surpresseur_controller.executeSurpresseurOn()

        # Should set timer to now + duration
        mock_surpresseur_controller.set_data.assert_any_call(
            "filtrationTempsRestant", 1000 + (10 * 60)
        )
        mock_surpresseur_controller.set_data.assert_any_call("filtrationSurpresseur", 1)
        mock_surpresseur_controller.activatingDevices.assert_called_once()
        mock_surpresseur_controller.startSecondCron.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_status_display(self, mock_surpresseur_controller):
        """Test executeSurpresseurOn updates status display with time remaining."""
        mock_surpresseur_controller.get_data = Mock(return_value=0)
        mock_surpresseur_controller.set_data = Mock()

        with patch('time.time', return_value=1000.0):
            await mock_surpresseur_controller.executeSurpresseurOn()

        # Status should be updated with "Actif : MM:SS"
        mock_surpresseur_controller.surpresseurStatus.set_status.assert_called_once()
        call_arg = mock_surpresseur_controller.surpresseurStatus.set_status.call_args[0][0]
        assert call_arg.startswith("Actif : ")

    @pytest.mark.asyncio
    async def test_skips_when_surpresseur_active(self, mock_surpresseur_controller):
        """Test executeSurpresseurOn skips when surpresseur already active."""
        # filtrationSurpresseur = 1 means already active
        mock_surpresseur_controller.get_data = Mock(side_effect=lambda key, default: 1 if key == "filtrationSurpresseur" else 0)
        mock_surpresseur_controller.set_data = Mock()

        await mock_surpresseur_controller.executeSurpresseurOn()

        # Should not set timer or activate
        mock_surpresseur_controller.set_data.assert_not_called()
        mock_surpresseur_controller.activatingDevices.assert_not_called()
        # But should still start cron
        mock_surpresseur_controller.startSecondCron.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_lavage_active(self, mock_surpresseur_controller):
        """Test executeSurpresseurOn skips when filter washing is active."""
        # filtrationLavageEtat = 1 means washing active
        mock_surpresseur_controller.get_data = Mock(side_effect=lambda key, default: 1 if key == "filtrationLavageEtat" else 0)
        mock_surpresseur_controller.set_data = Mock()

        await mock_surpresseur_controller.executeSurpresseurOn()

        # Should not set timer or activate
        mock_surpresseur_controller.set_data.assert_not_called()
        mock_surpresseur_controller.activatingDevices.assert_not_called()
        # But should still start cron
        mock_surpresseur_controller.startSecondCron.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculates_time_correctly(self, mock_surpresseur_controller):
        """Test executeSurpresseurOn calculates end time correctly."""
        mock_surpresseur_controller.get_data = Mock(return_value=0)
        mock_surpresseur_controller.set_data = Mock()
        mock_surpresseur_controller.surpresseurDuree = 15  # 15 minutes

        with patch('time.time', return_value=2000.0):
            await mock_surpresseur_controller.executeSurpresseurOn()

        # End time should be now + 15 * 60 = 2000 + 900 = 2900
        mock_surpresseur_controller.set_data.assert_any_call("filtrationTempsRestant", 2900)

    @pytest.mark.asyncio
    async def test_handles_no_status_object(self, mock_surpresseur_controller):
        """Test executeSurpresseurOn handles missing status object gracefully."""
        mock_surpresseur_controller.get_data = Mock(return_value=0)
        mock_surpresseur_controller.set_data = Mock()
        mock_surpresseur_controller.surpresseurStatus = None

        # Should not crash
        await mock_surpresseur_controller.executeSurpresseurOn()

        mock_surpresseur_controller.activatingDevices.assert_called_once()


@pytest.mark.unit
class TestRefreshSurpresseur:
    """Tests for refreshSurpresseur() - Refresh booster pump state."""

    @pytest.mark.asyncio
    async def test_refresh_calls_on_when_state_on(self, mock_surpresseur_controller):
        """Test refreshSurpresseur calls surpresseurOn when entity state is 'on'."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state
        mock_surpresseur_controller.surpresseurOn = AsyncMock()

        await mock_surpresseur_controller.refreshSurpresseur()

        mock_surpresseur_controller.surpresseurOn.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_refresh_calls_stop_when_state_off(self, mock_surpresseur_controller):
        """Test refreshSurpresseur calls surpresseurStop when entity state is 'off'."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state
        mock_surpresseur_controller.surpresseurStop = AsyncMock()

        await mock_surpresseur_controller.refreshSurpresseur()

        mock_surpresseur_controller.surpresseurStop.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_refresh_returns_early_without_config(self, mock_surpresseur_controller):
        """Test refreshSurpresseur returns early when surpresseur is not configured."""
        mock_surpresseur_controller.surpresseur = None

        await mock_surpresseur_controller.refreshSurpresseur()

        mock_surpresseur_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_returns_early_entity_not_found(self, mock_surpresseur_controller):
        """Test refreshSurpresseur returns early when entity is not found."""
        mock_surpresseur_controller.hass.states.get.return_value = None
        mock_surpresseur_controller.surpresseurOn = AsyncMock()

        await mock_surpresseur_controller.refreshSurpresseur()

        mock_surpresseur_controller.surpresseurOn.assert_not_called()


@pytest.mark.unit
class TestGetStateSurpresseur:
    """Tests for getStateSurpresseur() - Get booster pump state."""

    def test_returns_true_when_on(self, mock_surpresseur_controller):
        """Test getStateSurpresseur returns True when entity is on."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        result = mock_surpresseur_controller.getStateSurpresseur()

        assert result is True

    def test_returns_false_when_off(self, mock_surpresseur_controller):
        """Test getStateSurpresseur returns False when entity is off."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        result = mock_surpresseur_controller.getStateSurpresseur()

        assert result is False

    def test_returns_false_without_config(self, mock_surpresseur_controller):
        """Test getStateSurpresseur returns False when not configured."""
        mock_surpresseur_controller.surpresseur = None

        result = mock_surpresseur_controller.getStateSurpresseur()

        assert result is False
        mock_surpresseur_controller.hass.states.get.assert_not_called()

    def test_returns_false_entity_not_found(self, mock_surpresseur_controller):
        """Test getStateSurpresseur returns False when entity not found."""
        mock_surpresseur_controller.hass.states.get.return_value = None

        result = mock_surpresseur_controller.getStateSurpresseur()

        assert result is False

    def test_returns_bool_type(self, mock_surpresseur_controller):
        """Test getStateSurpresseur always returns boolean."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        result = mock_surpresseur_controller.getStateSurpresseur()

        assert isinstance(result, bool)


@pytest.mark.unit
class TestSurpresseurOn:
    """Tests for surpresseurOn() - Turn on booster pump."""

    @pytest.mark.asyncio
    async def test_calls_turn_on_service(self, mock_surpresseur_controller):
        """Test surpresseurOn calls turn_on service."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        await mock_surpresseur_controller.surpresseurOn()

        mock_surpresseur_controller.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_on",
            {"entity_id": "switch.surpresseur"}
        )

    @pytest.mark.asyncio
    async def test_skips_when_already_on(self, mock_surpresseur_controller):
        """Test surpresseurOn skips service call when already on and repeat=False."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        await mock_surpresseur_controller.surpresseurOn(repeat=False)

        mock_surpresseur_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_forces_when_repeat_true(self, mock_surpresseur_controller):
        """Test surpresseurOn calls service even when on if repeat=True."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        await mock_surpresseur_controller.surpresseurOn(repeat=True)

        mock_surpresseur_controller.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_early_without_config(self, mock_surpresseur_controller):
        """Test surpresseurOn returns early when not configured."""
        mock_surpresseur_controller.surpresseur = None

        await mock_surpresseur_controller.surpresseurOn()

        mock_surpresseur_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_early_entity_not_found(self, mock_surpresseur_controller):
        """Test surpresseurOn returns early when entity not found."""
        mock_surpresseur_controller.hass.states.get.return_value = None

        await mock_surpresseur_controller.surpresseurOn()

        mock_surpresseur_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_extracts_domain_correctly(self, mock_surpresseur_controller):
        """Test surpresseurOn extracts domain from entity_id correctly."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state
        mock_surpresseur_controller.surpresseur = "light.pool_booster"

        await mock_surpresseur_controller.surpresseurOn()

        mock_surpresseur_controller.hass.services.async_call.assert_called_once_with(
            "light",
            "turn_on",
            {"entity_id": "light.pool_booster"}
        )


@pytest.mark.unit
class TestSurpresseurStop:
    """Tests for surpresseurStop() - Turn off booster pump."""

    @pytest.mark.asyncio
    async def test_calls_turn_off_service(self, mock_surpresseur_controller):
        """Test surpresseurStop calls turn_off service."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        await mock_surpresseur_controller.surpresseurStop()

        mock_surpresseur_controller.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_off",
            {"entity_id": "switch.surpresseur"}
        )

    @pytest.mark.asyncio
    async def test_skips_when_already_off(self, mock_surpresseur_controller):
        """Test surpresseurStop skips service call when already off and repeat=False."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        await mock_surpresseur_controller.surpresseurStop(repeat=False)

        mock_surpresseur_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_forces_when_repeat_true(self, mock_surpresseur_controller):
        """Test surpresseurStop calls service even when off if repeat=True."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        await mock_surpresseur_controller.surpresseurStop(repeat=True)

        mock_surpresseur_controller.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_early_without_config(self, mock_surpresseur_controller):
        """Test surpresseurStop returns early when not configured."""
        mock_surpresseur_controller.surpresseur = None

        await mock_surpresseur_controller.surpresseurStop()

        mock_surpresseur_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_early_entity_not_found(self, mock_surpresseur_controller):
        """Test surpresseurStop returns early when entity not found."""
        mock_surpresseur_controller.hass.states.get.return_value = None

        await mock_surpresseur_controller.surpresseurStop()

        mock_surpresseur_controller.hass.services.async_call.assert_not_called()


@pytest.mark.integration
class TestSurpresseurIntegration:
    """Integration tests for booster pump control."""

    @pytest.mark.asyncio
    async def test_full_surpresseur_cycle(self, mock_surpresseur_controller):
        """Test complete on/off cycle for booster pump."""
        mock_state_off = MagicMock()
        mock_state_off.state = "off"

        mock_state_on = MagicMock()
        mock_state_on.state = "on"

        # Turn on, then off
        mock_surpresseur_controller.hass.states.get.side_effect = [
            mock_state_off,  # surpresseurOn check
            mock_state_on,   # surpresseurStop check
        ]

        await mock_surpresseur_controller.surpresseurOn()
        await mock_surpresseur_controller.surpresseurStop()

        # Verify both services were called
        assert mock_surpresseur_controller.hass.services.async_call.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_refresh(self, mock_surpresseur_controller):
        """Test executeSurpresseurOn followed by refresh."""
        mock_surpresseur_controller.get_data = Mock(return_value=0)
        mock_surpresseur_controller.set_data = Mock()
        mock_surpresseur_controller.surpresseurOn = AsyncMock()

        with patch('time.time', return_value=1000.0):
            await mock_surpresseur_controller.executeSurpresseurOn()

        # Verify state was set
        mock_surpresseur_controller.set_data.assert_any_call("filtrationSurpresseur", 1)

        # Now refresh should see it's active
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_surpresseur_controller.hass.states.get.return_value = mock_state

        await mock_surpresseur_controller.refreshSurpresseur()
        mock_surpresseur_controller.surpresseurOn.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_error_handling_no_entity(self, mock_surpresseur_controller):
        """Test graceful handling when entity doesn't exist."""
        mock_surpresseur_controller.hass.states.get.return_value = None

        # Should not crash for any function
        await mock_surpresseur_controller.refreshSurpresseur()
        state = mock_surpresseur_controller.getStateSurpresseur()
        await mock_surpresseur_controller.surpresseurOn()
        await mock_surpresseur_controller.surpresseurStop()

        assert state is False
        mock_surpresseur_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_timer_display_format(self, mock_surpresseur_controller):
        """Test that timer display formats time correctly."""
        mock_surpresseur_controller.get_data = Mock(return_value=0)
        mock_surpresseur_controller.set_data = Mock()
        mock_surpresseur_controller.surpresseurDuree = 5  # 5 minutes

        with patch('time.time', return_value=1000.0):
            await mock_surpresseur_controller.executeSurpresseurOn()

        # Check status was set with proper format
        status_call = mock_surpresseur_controller.surpresseurStatus.set_status.call_args[0][0]
        assert "Actif : " in status_call
        # Should show MM:SS format (5 minutes = 05:00)
        assert ":" in status_call.split("Actif : ")[1]

    @pytest.mark.asyncio
    async def test_concurrent_operation_prevention(self, mock_surpresseur_controller):
        """Test that surpresseur won't start during washing."""
        # Both surpresseur and lavage trying to be active
        def get_data_side_effect(key, default):
            if key == "filtrationSurpresseur":
                return 1  # Already active
            elif key == "filtrationLavageEtat":
                return 1  # Washing also active
            return 0

        mock_surpresseur_controller.get_data = Mock(side_effect=get_data_side_effect)
        mock_surpresseur_controller.set_data = Mock()

        await mock_surpresseur_controller.executeSurpresseurOn()

        # Should not activate or set timer
        mock_surpresseur_controller.set_data.assert_not_called()
        mock_surpresseur_controller.activatingDevices.assert_not_called()
