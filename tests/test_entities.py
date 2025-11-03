"""Tests for entities.py module."""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock, PropertyMock

# Skip all tests if homeassistant is not installed
pytest.importorskip(
    "homeassistant",
    reason="homeassistant package is required for these tests"
)


@pytest.mark.unit
class TestPoolControlStatusSensor:
    """Tests for PoolControlStatusSensor class."""

    @patch('custom_components.pool_control.entities.SensorEntity')
    def test_init_with_default_state(self, mock_sensor_entity, mock_pool_controller):
        """Test sensor initialization with default state."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Test Sensor",
            unique_id="test_sensor_1",
            controller_attribute_name="testSensor",
            default_state="Arrêté",
        )

        assert sensor._controller == mock_pool_controller
        assert sensor._attr_name == "Test Sensor"
        assert sensor._attr_unique_id == "test_sensor_1"
        assert sensor._controller_attribute_name == "testSensor"
        assert sensor._state == "Arrêté"
        assert sensor._ready is False

    @patch('custom_components.pool_control.entities.SensorEntity')
    def test_init_attaches_to_controller(self, mock_sensor_entity, mock_pool_controller):
        """Test that sensor attaches itself to controller on init."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Status Sensor",
            unique_id="status_1",
            controller_attribute_name="statusSensor",
        )

        # Verify the sensor was attached to the controller
        assert hasattr(mock_pool_controller, "statusSensor")
        assert getattr(mock_pool_controller, "statusSensor") == sensor

    @patch('custom_components.pool_control.entities.SensorEntity')
    def test_init_with_custom_default_state(self, mock_sensor_entity, mock_pool_controller):
        """Test sensor initialization with custom default state."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Custom Sensor",
            unique_id="custom_1",
            controller_attribute_name="customSensor",
            default_state="En marche",
        )

        assert sensor._state == "En marche"

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.SensorEntity')
    async def test_async_added_to_hass(self, mock_sensor_entity, mock_pool_controller):
        """Test async_added_to_hass sets ready flag."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Test",
            unique_id="test_1",
            controller_attribute_name="test",
        )

        assert sensor._ready is False

        await sensor.async_added_to_hass()

        assert sensor._ready is True

    @patch('custom_components.pool_control.entities.SensorEntity')
    def test_state_property(self, mock_sensor_entity, mock_pool_controller):
        """Test state property returns current state."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Test",
            unique_id="test_1",
            controller_attribute_name="test",
            default_state="Initial State",
        )

        assert sensor.state == "Initial State"

        # Change internal state
        sensor._state = "New State"
        assert sensor.state == "New State"

    @patch('custom_components.pool_control.entities.SensorEntity')
    def test_set_status_before_ready(self, mock_sensor_entity, mock_pool_controller):
        """Test set_status before sensor is ready (should not write to HA)."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Test",
            unique_id="test_1",
            controller_attribute_name="test",
            default_state="Initial",
        )

        # Mock async_write_ha_state
        sensor.async_write_ha_state = Mock()

        # Set status before ready
        sensor.set_status("New Status")

        assert sensor._state == "New Status"
        # Should not write to HA yet
        sensor.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.SensorEntity')
    async def test_set_status_after_ready(self, mock_sensor_entity, mock_pool_controller):
        """Test set_status after sensor is ready (should write to HA)."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Test",
            unique_id="test_1",
            controller_attribute_name="test",
            default_state="Initial",
        )

        # Mock async_write_ha_state
        sensor.async_write_ha_state = Mock()

        # Mark as ready
        await sensor.async_added_to_hass()

        # Set status after ready
        sensor.set_status("Active")

        assert sensor._state == "Active"
        # Should write to HA
        sensor.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.SensorEntity')
    async def test_set_status_multiple_times(self, mock_sensor_entity, mock_pool_controller):
        """Test setting status multiple times."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Test",
            unique_id="test_1",
            controller_attribute_name="test",
        )

        sensor.async_write_ha_state = Mock()
        await sensor.async_added_to_hass()

        sensor.set_status("State 1")
        assert sensor.state == "State 1"
        assert sensor.async_write_ha_state.call_count == 1

        sensor.set_status("State 2")
        assert sensor.state == "State 2"
        assert sensor.async_write_ha_state.call_count == 2

        sensor.set_status("State 3")
        assert sensor.state == "State 3"
        assert sensor.async_write_ha_state.call_count == 3

    @patch('custom_components.pool_control.entities.SensorEntity')
    def test_multiple_sensors_different_attributes(self, mock_sensor_entity, mock_pool_controller):
        """Test creating multiple sensors with different controller attributes."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor1 = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Sensor 1",
            unique_id="sensor_1",
            controller_attribute_name="sensor1",
        )

        sensor2 = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Sensor 2",
            unique_id="sensor_2",
            controller_attribute_name="sensor2",
        )

        # Verify both are attached
        assert mock_pool_controller.sensor1 == sensor1
        assert mock_pool_controller.sensor2 == sensor2
        assert sensor1 is not sensor2


@pytest.mark.unit
class TestPoolControlButton:
    """Tests for PoolControlButton class."""

    @patch('custom_components.pool_control.entities.ButtonEntity')
    def test_init(self, mock_button_entity, mock_pool_controller):
        """Test button initialization."""
        from custom_components.pool_control.entities import PoolControlButton

        callback = AsyncMock()

        button = PoolControlButton(
            controller=mock_pool_controller,
            name="Test Button",
            unique_id="test_button_1",
            callback=callback,
        )

        assert button._controller == mock_pool_controller
        assert button._attr_name == "Test Button"
        assert button._attr_unique_id == "test_button_1"
        assert button._callback == callback

    @patch('custom_components.pool_control.entities.ButtonEntity')
    def test_init_without_callback(self, mock_button_entity, mock_pool_controller):
        """Test button initialization without callback."""
        from custom_components.pool_control.entities import PoolControlButton

        button = PoolControlButton(
            controller=mock_pool_controller,
            name="No Callback Button",
            unique_id="no_callback",
            callback=None,
        )

        assert button._callback is None

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.ButtonEntity')
    async def test_async_press_calls_callback(self, mock_button_entity, mock_pool_controller):
        """Test async_press calls the callback."""
        from custom_components.pool_control.entities import PoolControlButton

        callback = AsyncMock()

        button = PoolControlButton(
            controller=mock_pool_controller,
            name="Press Test",
            unique_id="press_1",
            callback=callback,
        )

        await button.async_press()

        callback.assert_called_once()

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.ButtonEntity')
    async def test_async_press_without_callback(self, mock_button_entity, mock_pool_controller):
        """Test async_press without callback (should not error)."""
        from custom_components.pool_control.entities import PoolControlButton

        button = PoolControlButton(
            controller=mock_pool_controller,
            name="No Callback",
            unique_id="no_callback",
            callback=None,
        )

        # Should not raise any exception
        await button.async_press()

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.ButtonEntity')
    async def test_async_press_multiple_times(self, mock_button_entity, mock_pool_controller):
        """Test pressing button multiple times."""
        from custom_components.pool_control.entities import PoolControlButton

        callback = AsyncMock()

        button = PoolControlButton(
            controller=mock_pool_controller,
            name="Multi Press",
            unique_id="multi_press",
            callback=callback,
        )

        await button.async_press()
        await button.async_press()
        await button.async_press()

        assert callback.call_count == 3

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.ButtonEntity')
    async def test_async_press_with_controller_method(self, mock_button_entity, mock_pool_controller):
        """Test button with controller method as callback."""
        from custom_components.pool_control.entities import PoolControlButton

        # Setup controller with a test method
        mock_pool_controller.testMethod = AsyncMock()

        button = PoolControlButton(
            controller=mock_pool_controller,
            name="Controller Method Button",
            unique_id="controller_method",
            callback=mock_pool_controller.testMethod,
        )

        await button.async_press()

        mock_pool_controller.testMethod.assert_called_once()

    @patch('custom_components.pool_control.entities.ButtonEntity')
    def test_multiple_buttons_different_callbacks(self, mock_button_entity, mock_pool_controller):
        """Test creating multiple buttons with different callbacks."""
        from custom_components.pool_control.entities import PoolControlButton

        callback1 = AsyncMock()
        callback2 = AsyncMock()

        button1 = PoolControlButton(
            controller=mock_pool_controller,
            name="Button 1",
            unique_id="button_1",
            callback=callback1,
        )

        button2 = PoolControlButton(
            controller=mock_pool_controller,
            name="Button 2",
            unique_id="button_2",
            callback=callback2,
        )

        assert button1._callback == callback1
        assert button2._callback == callback2
        assert button1 is not button2

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.ButtonEntity')
    async def test_button_name_and_unique_id(self, mock_button_entity, mock_pool_controller):
        """Test button has correct name and unique_id attributes."""
        from custom_components.pool_control.entities import PoolControlButton

        button = PoolControlButton(
            controller=mock_pool_controller,
            name="Reset Button",
            unique_id="pool_control_reset",
            callback=AsyncMock(),
        )

        assert button._attr_name == "Reset Button"
        assert button._attr_unique_id == "pool_control_reset"


@pytest.mark.integration
class TestEntitiesIntegration:
    """Integration tests for entities working together."""

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.SensorEntity')
    @patch('custom_components.pool_control.entities.ButtonEntity')
    async def test_sensor_and_button_on_same_controller(self, mock_button_entity, mock_sensor_entity, mock_pool_controller):
        """Test sensor and button can coexist on the same controller."""
        from custom_components.pool_control.entities import PoolControlStatusSensor, PoolControlButton

        # Create sensor
        sensor = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Status",
            unique_id="status",
            controller_attribute_name="statusSensor",
            default_state="Arrêté",
        )

        # Create button with callback that updates sensor
        async def button_callback():
            sensor.set_status("En marche")

        button = PoolControlButton(
            controller=mock_pool_controller,
            name="Start",
            unique_id="start_button",
            callback=button_callback,
        )

        # Setup sensor
        sensor.async_write_ha_state = Mock()
        await sensor.async_added_to_hass()

        # Initial state
        assert sensor.state == "Arrêté"

        # Press button
        await button.async_press()

        # Sensor should be updated
        assert sensor.state == "En marche"
        sensor.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    @patch('custom_components.pool_control.entities.SensorEntity')
    async def test_multiple_sensors_updated_independently(self, mock_sensor_entity, mock_pool_controller):
        """Test multiple sensors can be updated independently."""
        from custom_components.pool_control.entities import PoolControlStatusSensor

        sensor1 = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Sensor 1",
            unique_id="sensor_1",
            controller_attribute_name="sensor1Status",
            default_state="Off",
        )

        sensor2 = PoolControlStatusSensor(
            controller=mock_pool_controller,
            name="Sensor 2",
            unique_id="sensor_2",
            controller_attribute_name="sensor2Status",
            default_state="Idle",
        )

        sensor1.async_write_ha_state = Mock()
        sensor2.async_write_ha_state = Mock()

        await sensor1.async_added_to_hass()
        await sensor2.async_added_to_hass()

        # Update sensor 1
        sensor1.set_status("On")
        assert sensor1.state == "On"
        assert sensor2.state == "Idle"
        assert sensor1.async_write_ha_state.call_count == 1
        assert sensor2.async_write_ha_state.call_count == 0

        # Update sensor 2
        sensor2.set_status("Active")
        assert sensor1.state == "On"
        assert sensor2.state == "Active"
        assert sensor1.async_write_ha_state.call_count == 1
        assert sensor2.async_write_ha_state.call_count == 1
