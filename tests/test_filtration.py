"""Tests for filtration.py module - Filtration control.

Tests the filtration control methods that manage the pool filtration system.

Functions tested:
1. refreshFiltration() - Refresh filtration state based on current entity state
2. filtrationOn(repeat=False) - Turn on filtration
3. filtrationStop(repeat=False) - Turn off filtration
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")


@pytest.fixture
def mock_filtration_controller(mock_hass, mock_pool_config):
    """Create a mock controller with FiltrationMixin."""
    from custom_components.pool_control.controller import PoolController

    controller = PoolController(mock_hass, mock_pool_config)

    # Mock filtration configuration
    controller.filtration = "switch.filtration"

    # Mock filtrationStatus
    controller.filtrationStatus = MagicMock()
    controller.filtrationStatus.set_status = Mock()

    return controller


@pytest.mark.unit
class TestRefreshFiltration:
    """Tests for refreshFiltration() - Refresh filtration state."""

    @pytest.mark.asyncio
    async def test_refresh_filtration_when_on(self, mock_filtration_controller):
        """Test refreshFiltration calls filtrationOn when entity state is 'on'."""
        # Mock entity state as 'on'
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_filtration_controller.hass.states.get.return_value = mock_state
        mock_filtration_controller.filtrationOn = AsyncMock()

        await mock_filtration_controller.refreshFiltration()

        mock_filtration_controller.filtrationOn.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_refresh_filtration_when_off(self, mock_filtration_controller):
        """Test refreshFiltration calls filtrationStop when entity state is 'off'."""
        # Mock entity state as 'off'
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_filtration_controller.hass.states.get.return_value = mock_state
        mock_filtration_controller.filtrationStop = AsyncMock()

        await mock_filtration_controller.refreshFiltration()

        mock_filtration_controller.filtrationStop.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_refresh_filtration_without_entity_id(self, mock_filtration_controller):
        """Test refreshFiltration returns early when filtration is not configured."""
        mock_filtration_controller.filtration = None

        await mock_filtration_controller.refreshFiltration()

        # Should not call hass.states.get
        mock_filtration_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_filtration_entity_not_found(self, mock_filtration_controller):
        """Test refreshFiltration returns early when entity is not found."""
        mock_filtration_controller.hass.states.get.return_value = None
        mock_filtration_controller.filtrationOn = AsyncMock()
        mock_filtration_controller.filtrationStop = AsyncMock()

        await mock_filtration_controller.refreshFiltration()

        # Should not call filtrationOn or filtrationStop
        mock_filtration_controller.filtrationOn.assert_not_called()
        mock_filtration_controller.filtrationStop.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_filtration_calls_states_get_with_entity_id(self, mock_filtration_controller):
        """Test refreshFiltration calls hass.states.get with correct entity_id."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_filtration_controller.hass.states.get.return_value = mock_state
        mock_filtration_controller.filtrationOn = AsyncMock()

        await mock_filtration_controller.refreshFiltration()

        mock_filtration_controller.hass.states.get.assert_called_once_with("switch.filtration")


@pytest.mark.unit
class TestFiltrationOn:
    """Tests for filtrationOn() - Turn on filtration."""

    @pytest.mark.asyncio
    async def test_filtration_on_turns_on_entity(self, mock_filtration_controller):
        """Test filtrationOn calls turn_on service."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_filtration_controller.hass.states.get.return_value = mock_state

        await mock_filtration_controller.filtrationOn()

        mock_filtration_controller.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_on",
            {"entity_id": "switch.filtration"}
        )

    @pytest.mark.asyncio
    async def test_filtration_on_updates_status(self, mock_filtration_controller):
        """Test filtrationOn updates filtrationStatus to 'Actif'."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_filtration_controller.hass.states.get.return_value = mock_state

        await mock_filtration_controller.filtrationOn()

        mock_filtration_controller.filtrationStatus.set_status.assert_called_once_with("Actif")

    @pytest.mark.asyncio
    async def test_filtration_on_skips_when_already_on(self, mock_filtration_controller):
        """Test filtrationOn skips service call when already on and repeat=False."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_filtration_controller.hass.states.get.return_value = mock_state

        await mock_filtration_controller.filtrationOn(repeat=False)

        # Should not call async_call
        mock_filtration_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_filtration_on_forces_when_repeat_true(self, mock_filtration_controller):
        """Test filtrationOn calls service even when already on if repeat=True."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_filtration_controller.hass.states.get.return_value = mock_state

        await mock_filtration_controller.filtrationOn(repeat=True)

        # Should call async_call even though already on
        mock_filtration_controller.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_filtration_on_without_entity_id(self, mock_filtration_controller):
        """Test filtrationOn returns early when filtration is not configured."""
        mock_filtration_controller.filtration = None

        await mock_filtration_controller.filtrationOn()

        # Should not call hass.states.get
        mock_filtration_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_filtration_on_entity_not_found(self, mock_filtration_controller):
        """Test filtrationOn returns early when entity is not found."""
        mock_filtration_controller.hass.states.get.return_value = None

        await mock_filtration_controller.filtrationOn()

        # Should not call async_call
        mock_filtration_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_filtration_on_extracts_domain_from_entity_id(self, mock_filtration_controller):
        """Test filtrationOn correctly extracts domain from entity_id."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_filtration_controller.hass.states.get.return_value = mock_state
        mock_filtration_controller.filtration = "custom_domain.my_filtration"

        await mock_filtration_controller.filtrationOn()

        # Should use extracted domain "custom_domain"
        mock_filtration_controller.hass.services.async_call.assert_called_once_with(
            "custom_domain",
            "turn_on",
            {"entity_id": "custom_domain.my_filtration"}
        )

    @pytest.mark.asyncio
    async def test_filtration_on_without_status_object(self, mock_filtration_controller):
        """Test filtrationOn doesn't crash when filtrationStatus is None."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_filtration_controller.hass.states.get.return_value = mock_state
        mock_filtration_controller.filtrationStatus = None

        await mock_filtration_controller.filtrationOn()

        # Should not crash
        mock_filtration_controller.hass.services.async_call.assert_called_once()


@pytest.mark.unit
class TestFiltrationStop:
    """Tests for filtrationStop() - Turn off filtration."""

    @pytest.mark.asyncio
    async def test_filtration_stop_turns_off_entity(self, mock_filtration_controller):
        """Test filtrationStop calls turn_off service."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_filtration_controller.hass.states.get.return_value = mock_state

        await mock_filtration_controller.filtrationStop()

        mock_filtration_controller.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_off",
            {"entity_id": "switch.filtration"}
        )

    @pytest.mark.asyncio
    async def test_filtration_stop_updates_status(self, mock_filtration_controller):
        """Test filtrationStop updates filtrationStatus to 'Arrêté'."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_filtration_controller.hass.states.get.return_value = mock_state

        await mock_filtration_controller.filtrationStop()

        mock_filtration_controller.filtrationStatus.set_status.assert_called_once_with("Arrêté")

    @pytest.mark.asyncio
    async def test_filtration_stop_skips_when_already_off(self, mock_filtration_controller):
        """Test filtrationStop skips service call when already off and repeat=False."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_filtration_controller.hass.states.get.return_value = mock_state

        await mock_filtration_controller.filtrationStop(repeat=False)

        # Should not call async_call
        mock_filtration_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_filtration_stop_forces_when_repeat_true(self, mock_filtration_controller):
        """Test filtrationStop calls service even when already off if repeat=True."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_filtration_controller.hass.states.get.return_value = mock_state

        await mock_filtration_controller.filtrationStop(repeat=True)

        # Should call async_call even though already off
        mock_filtration_controller.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_filtration_stop_without_entity_id(self, mock_filtration_controller):
        """Test filtrationStop returns early when filtration is not configured."""
        mock_filtration_controller.filtration = None

        await mock_filtration_controller.filtrationStop()

        # Should not call hass.states.get
        mock_filtration_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_filtration_stop_entity_not_found(self, mock_filtration_controller):
        """Test filtrationStop returns early when entity is not found."""
        mock_filtration_controller.hass.states.get.return_value = None

        await mock_filtration_controller.filtrationStop()

        # Should not call async_call
        mock_filtration_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_filtration_stop_extracts_domain_from_entity_id(self, mock_filtration_controller):
        """Test filtrationStop correctly extracts domain from entity_id."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_filtration_controller.hass.states.get.return_value = mock_state
        mock_filtration_controller.filtration = "light.pool_filtration"

        await mock_filtration_controller.filtrationStop()

        # Should use extracted domain "light"
        mock_filtration_controller.hass.services.async_call.assert_called_once_with(
            "light",
            "turn_off",
            {"entity_id": "light.pool_filtration"}
        )

    @pytest.mark.asyncio
    async def test_filtration_stop_without_status_object(self, mock_filtration_controller):
        """Test filtrationStop doesn't crash when filtrationStatus is None."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_filtration_controller.hass.states.get.return_value = mock_state
        mock_filtration_controller.filtrationStatus = None

        await mock_filtration_controller.filtrationStop()

        # Should not crash
        mock_filtration_controller.hass.services.async_call.assert_called_once()


@pytest.mark.integration
class TestFiltrationIntegration:
    """Integration tests for filtration control."""

    @pytest.mark.asyncio
    async def test_full_filtration_cycle(self, mock_filtration_controller):
        """Test complete filtration on/off cycle."""
        # Setup: filtration initially off
        mock_state_off = MagicMock()
        mock_state_off.state = "off"

        mock_state_on = MagicMock()
        mock_state_on.state = "on"

        # First call returns off, second call returns on
        mock_filtration_controller.hass.states.get.side_effect = [
            mock_state_off,  # First call (filtrationOn)
            mock_state_on,   # Second call (filtrationStop)
        ]

        # Turn on
        await mock_filtration_controller.filtrationOn()

        # Turn off
        await mock_filtration_controller.filtrationStop()

        # Verify both services were called
        assert mock_filtration_controller.hass.services.async_call.call_count == 2

        # Verify status updates
        calls = mock_filtration_controller.filtrationStatus.set_status.call_args_list
        assert calls[0][0][0] == "Actif"
        assert calls[1][0][0] == "Arrêté"

    @pytest.mark.asyncio
    async def test_refresh_then_control(self, mock_filtration_controller):
        """Test refreshFiltration followed by manual control."""
        # Setup: entity is off
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_filtration_controller.hass.states.get.return_value = mock_state
        mock_filtration_controller.filtrationStop = AsyncMock()

        # Refresh (should call stop since state is off)
        await mock_filtration_controller.refreshFiltration()

        mock_filtration_controller.filtrationStop.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_multiple_on_calls_without_repeat(self, mock_filtration_controller):
        """Test multiple filtrationOn calls are optimized when repeat=False."""
        mock_state_on = MagicMock()
        mock_state_on.state = "on"
        mock_filtration_controller.hass.states.get.return_value = mock_state_on

        # Call multiple times
        await mock_filtration_controller.filtrationOn()
        await mock_filtration_controller.filtrationOn()
        await mock_filtration_controller.filtrationOn()

        # Should not call service since already on
        mock_filtration_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_handling_missing_entity(self, mock_filtration_controller):
        """Test graceful handling when entity doesn't exist."""
        mock_filtration_controller.hass.states.get.return_value = None

        # Should not crash
        await mock_filtration_controller.refreshFiltration()
        await mock_filtration_controller.filtrationOn()
        await mock_filtration_controller.filtrationStop()

        # No service calls should have been made
        mock_filtration_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_handling_missing_configuration(self, mock_filtration_controller):
        """Test graceful handling when filtration is not configured."""
        mock_filtration_controller.filtration = None

        # Should not crash
        await mock_filtration_controller.refreshFiltration()
        await mock_filtration_controller.filtrationOn()
        await mock_filtration_controller.filtrationStop()

        # No service calls should have been made
        mock_filtration_controller.hass.services.async_call.assert_not_called()
