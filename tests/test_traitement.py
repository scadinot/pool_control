"""Tests for traitement.py module - Treatment control.

Tests the treatment control methods that manage pool water treatment devices.
The module handles two separate treatment devices (traitement and traitement_2).

Functions tested:
Traitement 1:
1. refreshTraitement() - Refresh treatment state
2. getStateTraitement() - Get treatment state (bool)
3. traitementOn(repeat=False) - Turn on treatment
4. traitementStop(repeat=False) - Turn off treatment

Traitement 2:
5. refreshTraitement_2() - Refresh treatment_2 state
6. getStateTraitement_2() - Get treatment_2 state (bool)
7. traitement_2_On(repeat=False) - Turn on treatment_2
8. traitement_2_Stop(repeat=False) - Turn off treatment_2
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")


@pytest.fixture
def mock_traitement_controller(mock_hass, mock_pool_config):
    """Create a mock controller with TraitementMixin."""
    from custom_components.pool_control.controller import PoolController

    controller = PoolController(mock_hass, mock_pool_config)

    # Mock traitement configuration
    controller.traitement = "switch.traitement"
    controller.traitement_2 = "switch.traitement_2"

    return controller


@pytest.mark.unit
class TestRefreshTraitement:
    """Tests for refreshTraitement() - Refresh treatment 1 state."""

    @pytest.mark.asyncio
    async def test_refresh_calls_on_when_state_on(self, mock_traitement_controller):
        """Test refreshTraitement calls traitementOn when entity state is 'on'."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state
        mock_traitement_controller.traitementOn = AsyncMock()

        await mock_traitement_controller.refreshTraitement()

        mock_traitement_controller.traitementOn.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_refresh_calls_stop_when_state_off(self, mock_traitement_controller):
        """Test refreshTraitement calls traitementStop when entity state is 'off'."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state
        mock_traitement_controller.traitementStop = AsyncMock()

        await mock_traitement_controller.refreshTraitement()

        mock_traitement_controller.traitementStop.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_refresh_returns_early_without_config(self, mock_traitement_controller):
        """Test refreshTraitement returns early when traitement is not configured."""
        mock_traitement_controller.traitement = None

        await mock_traitement_controller.refreshTraitement()

        mock_traitement_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_returns_early_entity_not_found(self, mock_traitement_controller):
        """Test refreshTraitement returns early when entity is not found."""
        mock_traitement_controller.hass.states.get.return_value = None
        mock_traitement_controller.traitementOn = AsyncMock()

        await mock_traitement_controller.refreshTraitement()

        mock_traitement_controller.traitementOn.assert_not_called()


@pytest.mark.unit
class TestGetStateTraitement:
    """Tests for getStateTraitement() - Get treatment 1 state."""

    def test_returns_true_when_on(self, mock_traitement_controller):
        """Test getStateTraitement returns True when entity is on."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        result = mock_traitement_controller.getStateTraitement()

        assert result is True

    def test_returns_false_when_off(self, mock_traitement_controller):
        """Test getStateTraitement returns False when entity is off."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        result = mock_traitement_controller.getStateTraitement()

        assert result is False

    def test_returns_false_without_config(self, mock_traitement_controller):
        """Test getStateTraitement returns False when not configured."""
        mock_traitement_controller.traitement = None

        result = mock_traitement_controller.getStateTraitement()

        assert result is False
        mock_traitement_controller.hass.states.get.assert_not_called()

    def test_returns_false_entity_not_found(self, mock_traitement_controller):
        """Test getStateTraitement returns False when entity not found."""
        mock_traitement_controller.hass.states.get.return_value = None

        result = mock_traitement_controller.getStateTraitement()

        assert result is False

    def test_returns_bool_type(self, mock_traitement_controller):
        """Test getStateTraitement always returns boolean."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        result = mock_traitement_controller.getStateTraitement()

        assert isinstance(result, bool)


@pytest.mark.unit
class TestTraitementOn:
    """Tests for traitementOn() - Turn on treatment 1."""

    @pytest.mark.asyncio
    async def test_calls_turn_on_service(self, mock_traitement_controller):
        """Test traitementOn calls turn_on service."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitementOn()

        mock_traitement_controller.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_on",
            {"entity_id": "switch.traitement"}
        )

    @pytest.mark.asyncio
    async def test_skips_when_already_on(self, mock_traitement_controller):
        """Test traitementOn skips service call when already on and repeat=False."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitementOn(repeat=False)

        mock_traitement_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_forces_when_repeat_true(self, mock_traitement_controller):
        """Test traitementOn calls service even when on if repeat=True."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitementOn(repeat=True)

        mock_traitement_controller.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_early_without_config(self, mock_traitement_controller):
        """Test traitementOn returns early when not configured."""
        mock_traitement_controller.traitement = None

        await mock_traitement_controller.traitementOn()

        mock_traitement_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_early_entity_not_found(self, mock_traitement_controller):
        """Test traitementOn returns early when entity not found."""
        mock_traitement_controller.hass.states.get.return_value = None

        await mock_traitement_controller.traitementOn()

        mock_traitement_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_extracts_domain_correctly(self, mock_traitement_controller):
        """Test traitementOn extracts domain from entity_id correctly."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state
        mock_traitement_controller.traitement = "light.pool_treatment"

        await mock_traitement_controller.traitementOn()

        mock_traitement_controller.hass.services.async_call.assert_called_once_with(
            "light",
            "turn_on",
            {"entity_id": "light.pool_treatment"}
        )


@pytest.mark.unit
class TestTraitementStop:
    """Tests for traitementStop() - Turn off treatment 1."""

    @pytest.mark.asyncio
    async def test_calls_turn_off_service(self, mock_traitement_controller):
        """Test traitementStop calls turn_off service."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitementStop()

        mock_traitement_controller.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_off",
            {"entity_id": "switch.traitement"}
        )

    @pytest.mark.asyncio
    async def test_skips_when_already_off(self, mock_traitement_controller):
        """Test traitementStop skips service call when already off and repeat=False."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitementStop(repeat=False)

        mock_traitement_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_forces_when_repeat_true(self, mock_traitement_controller):
        """Test traitementStop calls service even when off if repeat=True."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitementStop(repeat=True)

        mock_traitement_controller.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_early_without_config(self, mock_traitement_controller):
        """Test traitementStop returns early when not configured."""
        mock_traitement_controller.traitement = None

        await mock_traitement_controller.traitementStop()

        mock_traitement_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_early_entity_not_found(self, mock_traitement_controller):
        """Test traitementStop returns early when entity not found."""
        mock_traitement_controller.hass.states.get.return_value = None

        await mock_traitement_controller.traitementStop()

        mock_traitement_controller.hass.services.async_call.assert_not_called()


@pytest.mark.unit
class TestRefreshTraitement2:
    """Tests for refreshTraitement_2() - Refresh treatment 2 state."""

    @pytest.mark.asyncio
    async def test_refresh_calls_on_when_state_on(self, mock_traitement_controller):
        """Test refreshTraitement_2 calls traitement_2_On when entity state is 'on'."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state
        mock_traitement_controller.traitement_2_On = AsyncMock()

        await mock_traitement_controller.refreshTraitement_2()

        mock_traitement_controller.traitement_2_On.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_refresh_calls_stop_when_state_off(self, mock_traitement_controller):
        """Test refreshTraitement_2 calls traitement_2_Stop when entity state is 'off'."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state
        mock_traitement_controller.traitement_2_Stop = AsyncMock()

        await mock_traitement_controller.refreshTraitement_2()

        mock_traitement_controller.traitement_2_Stop.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_refresh_returns_early_without_config(self, mock_traitement_controller):
        """Test refreshTraitement_2 returns early when traitement_2 is not configured."""
        mock_traitement_controller.traitement_2 = None

        await mock_traitement_controller.refreshTraitement_2()

        mock_traitement_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_returns_early_entity_not_found(self, mock_traitement_controller):
        """Test refreshTraitement_2 returns early when entity is not found."""
        mock_traitement_controller.hass.states.get.return_value = None
        mock_traitement_controller.traitement_2_On = AsyncMock()

        await mock_traitement_controller.refreshTraitement_2()

        mock_traitement_controller.traitement_2_On.assert_not_called()


@pytest.mark.unit
class TestGetStateTraitement2:
    """Tests for getStateTraitement_2() - Get treatment 2 state."""

    def test_returns_true_when_on(self, mock_traitement_controller):
        """Test getStateTraitement_2 returns True when entity is on."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        result = mock_traitement_controller.getStateTraitement_2()

        assert result is True

    def test_returns_false_when_off(self, mock_traitement_controller):
        """Test getStateTraitement_2 returns False when entity is off."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        result = mock_traitement_controller.getStateTraitement_2()

        assert result is False

    def test_returns_false_without_config(self, mock_traitement_controller):
        """Test getStateTraitement_2 returns False when not configured."""
        mock_traitement_controller.traitement_2 = None

        result = mock_traitement_controller.getStateTraitement_2()

        assert result is False
        mock_traitement_controller.hass.states.get.assert_not_called()

    def test_returns_false_entity_not_found(self, mock_traitement_controller):
        """Test getStateTraitement_2 returns False when entity not found."""
        mock_traitement_controller.hass.states.get.return_value = None

        result = mock_traitement_controller.getStateTraitement_2()

        assert result is False

    def test_returns_bool_type(self, mock_traitement_controller):
        """Test getStateTraitement_2 always returns boolean."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        result = mock_traitement_controller.getStateTraitement_2()

        assert isinstance(result, bool)


@pytest.mark.unit
class TestTraitement2On:
    """Tests for traitement_2_On() - Turn on treatment 2."""

    @pytest.mark.asyncio
    async def test_calls_turn_on_service(self, mock_traitement_controller):
        """Test traitement_2_On calls turn_on service."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitement_2_On()

        mock_traitement_controller.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_on",
            {"entity_id": "switch.traitement_2"}
        )

    @pytest.mark.asyncio
    async def test_skips_when_already_on(self, mock_traitement_controller):
        """Test traitement_2_On skips service call when already on and repeat=False."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitement_2_On(repeat=False)

        mock_traitement_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_forces_when_repeat_true(self, mock_traitement_controller):
        """Test traitement_2_On calls service even when on if repeat=True."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitement_2_On(repeat=True)

        mock_traitement_controller.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_early_without_config(self, mock_traitement_controller):
        """Test traitement_2_On returns early when not configured."""
        mock_traitement_controller.traitement_2 = None

        await mock_traitement_controller.traitement_2_On()

        mock_traitement_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_early_entity_not_found(self, mock_traitement_controller):
        """Test traitement_2_On returns early when entity not found."""
        mock_traitement_controller.hass.states.get.return_value = None

        await mock_traitement_controller.traitement_2_On()

        mock_traitement_controller.hass.services.async_call.assert_not_called()


@pytest.mark.unit
class TestTraitement2Stop:
    """Tests for traitement_2_Stop() - Turn off treatment 2."""

    @pytest.mark.asyncio
    async def test_calls_turn_off_service(self, mock_traitement_controller):
        """Test traitement_2_Stop calls turn_off service."""
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitement_2_Stop()

        mock_traitement_controller.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_off",
            {"entity_id": "switch.traitement_2"}
        )

    @pytest.mark.asyncio
    async def test_skips_when_already_off(self, mock_traitement_controller):
        """Test traitement_2_Stop skips service call when already off and repeat=False."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitement_2_Stop(repeat=False)

        mock_traitement_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_forces_when_repeat_true(self, mock_traitement_controller):
        """Test traitement_2_Stop calls service even when off if repeat=True."""
        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        await mock_traitement_controller.traitement_2_Stop(repeat=True)

        mock_traitement_controller.hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_early_without_config(self, mock_traitement_controller):
        """Test traitement_2_Stop returns early when not configured."""
        mock_traitement_controller.traitement_2 = None

        await mock_traitement_controller.traitement_2_Stop()

        mock_traitement_controller.hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_early_entity_not_found(self, mock_traitement_controller):
        """Test traitement_2_Stop returns early when entity not found."""
        mock_traitement_controller.hass.states.get.return_value = None

        await mock_traitement_controller.traitement_2_Stop()

        mock_traitement_controller.hass.services.async_call.assert_not_called()


@pytest.mark.integration
class TestTraitementIntegration:
    """Integration tests for treatment control."""

    @pytest.mark.asyncio
    async def test_both_treatments_independent(self, mock_traitement_controller):
        """Test traitement and traitement_2 can be controlled independently."""
        # Setup different states for each
        def get_state_side_effect(entity_id):
            mock_state = MagicMock()
            if entity_id == "switch.traitement":
                mock_state.state = "off"
            elif entity_id == "switch.traitement_2":
                mock_state.state = "on"
            return mock_state

        mock_traitement_controller.hass.states.get.side_effect = get_state_side_effect

        # Get states
        state1 = mock_traitement_controller.getStateTraitement()
        state2 = mock_traitement_controller.getStateTraitement_2()

        assert state1 is False
        assert state2 is True

    @pytest.mark.asyncio
    async def test_full_treatment_cycle(self, mock_traitement_controller):
        """Test complete on/off cycle for treatment."""
        mock_state_off = MagicMock()
        mock_state_off.state = "off"

        mock_state_on = MagicMock()
        mock_state_on.state = "on"

        # Turn on, then off
        mock_traitement_controller.hass.states.get.side_effect = [
            mock_state_off,  # traitementOn check
            mock_state_on,   # traitementStop check
        ]

        await mock_traitement_controller.traitementOn()
        await mock_traitement_controller.traitementStop()

        # Verify both services were called
        assert mock_traitement_controller.hass.services.async_call.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handling_both_devices(self, mock_traitement_controller):
        """Test graceful handling when both devices don't exist."""
        mock_traitement_controller.hass.states.get.return_value = None

        # Should not crash for any function
        await mock_traitement_controller.refreshTraitement()
        await mock_traitement_controller.refreshTraitement_2()
        state1 = mock_traitement_controller.getStateTraitement()
        state2 = mock_traitement_controller.getStateTraitement_2()
        await mock_traitement_controller.traitementOn()
        await mock_traitement_controller.traitement_2_On()

        assert state1 is False
        assert state2 is False
        mock_traitement_controller.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_configuration(self, mock_traitement_controller):
        """Test system works with only one treatment configured."""
        # Only traitement configured, not traitement_2
        mock_traitement_controller.traitement_2 = None

        mock_state = MagicMock()
        mock_state.state = "off"
        mock_traitement_controller.hass.states.get.return_value = mock_state

        # Treatment 1 should work
        await mock_traitement_controller.traitementOn()
        assert mock_traitement_controller.hass.services.async_call.call_count == 1

        # Treatment 2 should return early without errors
        await mock_traitement_controller.traitement_2_On()
        # Call count should still be 1 (no new call)
        assert mock_traitement_controller.hass.services.async_call.call_count == 1
