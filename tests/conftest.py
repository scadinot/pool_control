"""Fixtures communes pour les tests Pool Control."""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, time

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from tests.const import MOCK_CONFIG_FULL, MOCK_CONFIG_MINIMAL


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance.

    Crée un mock de Home Assistant avec les méthodes essentielles.
    """
    hass = MagicMock(spec=HomeAssistant)

    # Mock des services
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()

    # Mock des états
    hass.states = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    hass.states.async_set = AsyncMock()

    # Data storage
    hass.data = {}

    # Loop (pour asyncio)
    hass.loop = MagicMock()

    return hass


@pytest.fixture
def mock_config_entry():
    """Mock configuration entry.

    Crée un ConfigEntry mock pour les tests.
    """
    return ConfigEntry(
        version=1,
        domain="pool_control",
        title="Pool Control",
        data={},
        source="user",
        entry_id="test_entry_id",
        unique_id="test_unique_id",
    )


@pytest.fixture
def mock_pool_config_minimal():
    """Configuration minimale pour les tests rapides."""
    return MOCK_CONFIG_MINIMAL.copy()


@pytest.fixture
def mock_pool_config():
    """Configuration complète pour les tests."""
    return MOCK_CONFIG_FULL.copy()


@pytest.fixture
def mock_state_factory():
    """Factory pour créer des mocks d'états d'entités.

    Usage:
        state = mock_state_factory("sensor.temperature", "25.5")
    """
    def _create_state(entity_id: str, state: str, attributes: dict = None):
        """Crée un mock de state."""
        mock = MagicMock()
        mock.entity_id = entity_id
        mock.state = state
        mock.attributes = attributes or {}
        mock.last_changed = datetime.now()
        mock.last_updated = datetime.now()
        return mock

    return _create_state


@pytest.fixture
def mock_switch_on(mock_state_factory):
    """Mock d'un switch en état 'on'."""
    return mock_state_factory("switch.test", "on")


@pytest.fixture
def mock_switch_off(mock_state_factory):
    """Mock d'un switch en état 'off'."""
    return mock_state_factory("switch.test", "off")


@pytest.fixture
def mock_temperature_sensor(mock_state_factory):
    """Mock d'un capteur de température."""
    def _create_temp_sensor(temperature: float):
        return mock_state_factory(
            "sensor.pool_temperature",
            str(temperature),
            {"unit_of_measurement": "°C"}
        )
    return _create_temp_sensor


@pytest.fixture
def setup_hass_states(mock_hass, mock_state_factory):
    """Helper pour configurer plusieurs états dans mock_hass.

    Usage:
        setup_hass_states({
            "switch.filtration": "on",
            "sensor.temperature": "25.5",
        })
    """
    def _setup(states: dict):
        """Configure les états dans le mock hass."""
        def get_state(entity_id):
            state_value = states.get(entity_id)
            if state_value is None:
                return None
            return mock_state_factory(entity_id, str(state_value))

        mock_hass.states.get.side_effect = get_state
        return mock_hass

    return _setup


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integration loading for all tests.

    Cette fixture est fournie par pytest-homeassistant-custom-component.
    """
    yield
