"""Tests for sensors.py module (SensorMixin)."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Skip all tests if homeassistant is not installed
pytest.importorskip(
    "homeassistant",
    reason="homeassistant package is required for these tests"
)


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

    def test_get_lever_soleil_state_not_found(self, mock_pool_controller):
        """Test when sunrise sensor state is not found."""
        mock_pool_controller.hass.states.get.return_value = None

        result = mock_pool_controller.getLeverSoleil()

        # Should return default value
        assert result == "06:00"


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

        # Verify state was NOT set
        mock_pool_controller.hass.states.async_set.assert_not_called()


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
