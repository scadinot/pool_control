"""Tests for sensors.py module (SensorMixin)."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Skip all tests if homeassistant is not installed
pytest.importorskip(
    "homeassistant",
    reason="homeassistant package is required for these tests"
)

from custom_components.pool_control.sensors import SensorMixin


@pytest.mark.unit
class TestSensorMixinGetTemperatureWater:
    """Tests for SensorMixin.getTemperatureWater() method."""

    def test_get_temperature_water_valid(self, mock_pool_controller):
        """Test getting valid water temperature."""
        # Setup mock state
        temp_state = Mock()
        temp_state.state = "25.5"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureWater()

        assert result == 25.5
        mock_pool_controller.hass.states.get.assert_called_once_with(
            mock_pool_controller.temperatureWater
        )

    def test_get_temperature_water_integer(self, mock_pool_controller):
        """Test getting integer water temperature."""
        temp_state = Mock()
        temp_state.state = "20"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureWater()

        assert result == 20.0
        assert isinstance(result, float)

    def test_get_temperature_water_zero(self, mock_pool_controller):
        """Test getting zero water temperature."""
        temp_state = Mock()
        temp_state.state = "0"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureWater()

        assert result == 0.0

    def test_get_temperature_water_negative(self, mock_pool_controller):
        """Test getting negative water temperature."""
        temp_state = Mock()
        temp_state.state = "-5.5"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureWater()

        assert result == -5.5

    def test_get_temperature_water_state_not_found(self, mock_pool_controller):
        """Test when temperature sensor state is not found."""
        mock_pool_controller.hass.states.get.return_value = None

        result = mock_pool_controller.getTemperatureWater()

        assert result == 0.0

    def test_get_temperature_water_invalid_value(self, mock_pool_controller):
        """Test when temperature value is invalid."""
        temp_state = Mock()
        temp_state.state = "invalid"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureWater()

        assert result == 0.0

    def test_get_temperature_water_empty_string(self, mock_pool_controller):
        """Test when temperature value is empty string."""
        temp_state = Mock()
        temp_state.state = ""
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureWater()

        assert result == 0.0

    def test_get_temperature_water_unavailable(self, mock_pool_controller):
        """Test when temperature sensor is unavailable."""
        temp_state = Mock()
        temp_state.state = "unavailable"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureWater()

        assert result == 0.0

    def test_get_temperature_water_large_value(self, mock_pool_controller):
        """Test getting large water temperature value."""
        temp_state = Mock()
        temp_state.state = "99.9"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureWater()

        assert result == 99.9


@pytest.mark.unit
class TestSensorMixinGetTemperatureOutdoor:
    """Tests for SensorMixin.getTemperatureOutdoor() method."""

    def test_get_temperature_outdoor_valid(self, mock_pool_controller):
        """Test getting valid outdoor temperature."""
        temp_state = Mock()
        temp_state.state = "18.3"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureOutdoor()

        assert result == 18.3
        mock_pool_controller.hass.states.get.assert_called_once_with(
            mock_pool_controller.temperatureOutdoor
        )

    def test_get_temperature_outdoor_integer(self, mock_pool_controller):
        """Test getting integer outdoor temperature."""
        temp_state = Mock()
        temp_state.state = "15"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureOutdoor()

        assert result == 15.0
        assert isinstance(result, float)

    def test_get_temperature_outdoor_zero(self, mock_pool_controller):
        """Test getting zero outdoor temperature."""
        temp_state = Mock()
        temp_state.state = "0"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureOutdoor()

        assert result == 0.0

    def test_get_temperature_outdoor_negative(self, mock_pool_controller):
        """Test getting negative outdoor temperature."""
        temp_state = Mock()
        temp_state.state = "-10.5"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureOutdoor()

        assert result == -10.5

    def test_get_temperature_outdoor_state_not_found(self, mock_pool_controller):
        """Test when outdoor temperature sensor state is not found."""
        mock_pool_controller.hass.states.get.return_value = None

        result = mock_pool_controller.getTemperatureOutdoor()

        assert result == 0.0

    def test_get_temperature_outdoor_invalid_value(self, mock_pool_controller):
        """Test when outdoor temperature value is invalid."""
        temp_state = Mock()
        temp_state.state = "not_a_number"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureOutdoor()

        assert result == 0.0

    def test_get_temperature_outdoor_empty_string(self, mock_pool_controller):
        """Test when outdoor temperature value is empty string."""
        temp_state = Mock()
        temp_state.state = ""
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureOutdoor()

        assert result == 0.0

    def test_get_temperature_outdoor_unavailable(self, mock_pool_controller):
        """Test when outdoor temperature sensor is unavailable."""
        temp_state = Mock()
        temp_state.state = "unavailable"
        mock_pool_controller.hass.states.get.return_value = temp_state

        result = mock_pool_controller.getTemperatureOutdoor()

        assert result == 0.0


@pytest.mark.unit
class TestSensorMixinGetLeverSoleil:
    """Tests for SensorMixin.getLeverSoleil() method."""

    def test_get_lever_soleil_valid_iso_format(self, mock_pool_controller):
        """Test getting sunrise time in ISO format."""
        sunrise_state = Mock()
        sunrise_state.state = "2025-11-03T06:30:00+00:00"
        mock_pool_controller.hass.states.get.return_value = sunrise_state

        result = mock_pool_controller.getLeverSoleil()

        assert result == "06:30"
        mock_pool_controller.hass.states.get.assert_called_once_with(
            mock_pool_controller.leverSoleil
        )

    def test_get_lever_soleil_early_morning(self, mock_pool_controller):
        """Test getting early morning sunrise time."""
        sunrise_state = Mock()
        sunrise_state.state = "2025-06-21T05:15:00+00:00"
        mock_pool_controller.hass.states.get.return_value = sunrise_state

        result = mock_pool_controller.getLeverSoleil()

        assert result == "05:15"

    def test_get_lever_soleil_late_morning(self, mock_pool_controller):
        """Test getting late morning sunrise time."""
        sunrise_state = Mock()
        sunrise_state.state = "2025-12-21T08:45:00+00:00"
        mock_pool_controller.hass.states.get.return_value = sunrise_state

        result = mock_pool_controller.getLeverSoleil()

        assert result == "08:45"

    def test_get_lever_soleil_exact_hour(self, mock_pool_controller):
        """Test getting sunrise at exact hour."""
        sunrise_state = Mock()
        sunrise_state.state = "2025-11-03T07:00:00+00:00"
        mock_pool_controller.hass.states.get.return_value = sunrise_state

        result = mock_pool_controller.getLeverSoleil()

        assert result == "07:00"

    def test_get_lever_soleil_state_not_found(self, mock_pool_controller):
        """Test when sunrise sensor state is not found."""
        mock_pool_controller.hass.states.get.return_value = None

        result = mock_pool_controller.getLeverSoleil()

        # Should return default value
        assert result == "06:00"

    def test_get_lever_soleil_with_timezone(self, mock_pool_controller):
        """Test getting sunrise with different timezone."""
        sunrise_state = Mock()
        sunrise_state.state = "2025-11-03T06:45:00+01:00"
        mock_pool_controller.hass.states.get.return_value = sunrise_state

        result = mock_pool_controller.getLeverSoleil()

        assert result == "06:45"

    def test_get_lever_soleil_without_timezone(self, mock_pool_controller):
        """Test getting sunrise without timezone info."""
        sunrise_state = Mock()
        sunrise_state.state = "2025-11-03T06:20:00"
        mock_pool_controller.hass.states.get.return_value = sunrise_state

        result = mock_pool_controller.getLeverSoleil()

        assert result == "06:20"

    def test_get_lever_soleil_midnight(self, mock_pool_controller):
        """Test getting sunrise at midnight (edge case)."""
        sunrise_state = Mock()
        sunrise_state.state = "2025-11-03T00:00:00+00:00"
        mock_pool_controller.hass.states.get.return_value = sunrise_state

        result = mock_pool_controller.getLeverSoleil()

        assert result == "00:00"

    def test_get_lever_soleil_noon(self, mock_pool_controller):
        """Test getting sunrise at noon (edge case)."""
        sunrise_state = Mock()
        sunrise_state.state = "2025-11-03T12:00:00+00:00"
        mock_pool_controller.hass.states.get.return_value = sunrise_state

        result = mock_pool_controller.getLeverSoleil()

        assert result == "12:00"


@pytest.mark.unit
class TestSensorMixinUpdateTemperatureDisplay:
    """Tests for SensorMixin.updateTemperatureDisplay() method."""

    def test_update_temperature_display_entity_exists(self, mock_pool_controller):
        """Test updating temperature display when entity exists."""
        # Setup mock state to exist
        display_state = Mock()
        mock_pool_controller.hass.states.get.return_value = display_state
        mock_pool_controller.hass.states.async_set = Mock()

        mock_pool_controller.updateTemperatureDisplay(25.5)

        # Verify entity was checked
        mock_pool_controller.hass.states.get.assert_called_once_with(
            "input_number.temperatureDisplay"
        )

        # Verify state was set
        mock_pool_controller.hass.states.async_set.assert_called_once_with(
            "input_number.temperatureDisplay", 25.5
        )

    def test_update_temperature_display_entity_not_exists(self, mock_pool_controller):
        """Test updating temperature display when entity does not exist."""
        # Setup mock state to not exist
        mock_pool_controller.hass.states.get.return_value = None
        mock_pool_controller.hass.states.async_set = Mock()

        # Should not raise exception
        mock_pool_controller.updateTemperatureDisplay(20.0)

        # Verify entity was checked
        mock_pool_controller.hass.states.get.assert_called_once_with(
            "input_number.temperatureDisplay"
        )

        # Verify state was NOT set
        mock_pool_controller.hass.states.async_set.assert_not_called()

    def test_update_temperature_display_integer(self, mock_pool_controller):
        """Test updating display with integer temperature."""
        display_state = Mock()
        mock_pool_controller.hass.states.get.return_value = display_state
        mock_pool_controller.hass.states.async_set = Mock()

        mock_pool_controller.updateTemperatureDisplay(20)

        mock_pool_controller.hass.states.async_set.assert_called_once_with(
            "input_number.temperatureDisplay", 20
        )

    def test_update_temperature_display_zero(self, mock_pool_controller):
        """Test updating display with zero temperature."""
        display_state = Mock()
        mock_pool_controller.hass.states.get.return_value = display_state
        mock_pool_controller.hass.states.async_set = Mock()

        mock_pool_controller.updateTemperatureDisplay(0.0)

        mock_pool_controller.hass.states.async_set.assert_called_once_with(
            "input_number.temperatureDisplay", 0.0
        )

    def test_update_temperature_display_negative(self, mock_pool_controller):
        """Test updating display with negative temperature."""
        display_state = Mock()
        mock_pool_controller.hass.states.get.return_value = display_state
        mock_pool_controller.hass.states.async_set = Mock()

        mock_pool_controller.updateTemperatureDisplay(-5.5)

        mock_pool_controller.hass.states.async_set.assert_called_once_with(
            "input_number.temperatureDisplay", -5.5
        )

    def test_update_temperature_display_multiple_times(self, mock_pool_controller):
        """Test updating display multiple times."""
        display_state = Mock()
        mock_pool_controller.hass.states.get.return_value = display_state
        mock_pool_controller.hass.states.async_set = Mock()

        mock_pool_controller.updateTemperatureDisplay(20.0)
        mock_pool_controller.updateTemperatureDisplay(25.5)
        mock_pool_controller.updateTemperatureDisplay(30.0)

        assert mock_pool_controller.hass.states.async_set.call_count == 3


@pytest.mark.integration
class TestSensorMixinIntegration:
    """Integration tests for SensorMixin methods working together."""

    def test_get_both_temperatures(self, mock_pool_controller):
        """Test getting both water and outdoor temperatures."""
        # Setup mock states
        water_state = Mock()
        water_state.state = "25.0"

        outdoor_state = Mock()
        outdoor_state.state = "18.5"

        def get_state(entity_id):
            if entity_id == mock_pool_controller.temperatureWater:
                return water_state
            elif entity_id == mock_pool_controller.temperatureOutdoor:
                return outdoor_state
            return None

        mock_pool_controller.hass.states.get.side_effect = get_state

        water_temp = mock_pool_controller.getTemperatureWater()
        outdoor_temp = mock_pool_controller.getTemperatureOutdoor()

        assert water_temp == 25.0
        assert outdoor_temp == 18.5
        assert water_temp > outdoor_temp

    def test_get_all_sensor_values(self, mock_pool_controller):
        """Test getting all sensor values at once."""
        # Setup mock states
        water_state = Mock()
        water_state.state = "22.5"

        outdoor_state = Mock()
        outdoor_state.state = "15.0"

        sunrise_state = Mock()
        sunrise_state.state = "2025-11-03T06:30:00+00:00"

        def get_state(entity_id):
            if entity_id == mock_pool_controller.temperatureWater:
                return water_state
            elif entity_id == mock_pool_controller.temperatureOutdoor:
                return outdoor_state
            elif entity_id == mock_pool_controller.leverSoleil:
                return sunrise_state
            return None

        mock_pool_controller.hass.states.get.side_effect = get_state

        water = mock_pool_controller.getTemperatureWater()
        outdoor = mock_pool_controller.getTemperatureOutdoor()
        sunrise = mock_pool_controller.getLeverSoleil()

        assert water == 22.5
        assert outdoor == 15.0
        assert sunrise == "06:30"

    def test_sensor_error_handling_combination(self, mock_pool_controller):
        """Test error handling when some sensors fail."""
        # Setup: water valid, outdoor invalid, sunrise missing
        water_state = Mock()
        water_state.state = "23.0"

        outdoor_state = Mock()
        outdoor_state.state = "invalid"

        def get_state(entity_id):
            if entity_id == mock_pool_controller.temperatureWater:
                return water_state
            elif entity_id == mock_pool_controller.temperatureOutdoor:
                return outdoor_state
            elif entity_id == mock_pool_controller.leverSoleil:
                return None  # Sunrise not found
            return None

        mock_pool_controller.hass.states.get.side_effect = get_state

        water = mock_pool_controller.getTemperatureWater()
        outdoor = mock_pool_controller.getTemperatureOutdoor()
        sunrise = mock_pool_controller.getLeverSoleil()

        # Valid water temp
        assert water == 23.0
        # Invalid outdoor returns 0.0
        assert outdoor == 0.0
        # Missing sunrise returns default
        assert sunrise == "06:00"
