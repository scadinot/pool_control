"""Tests pour valider l'environnement de test."""
import pytest


class TestEnvironmentSetup:
    """Vérifie que l'environnement de test est correctement configuré."""

    def test_pytest_works(self):
        """Test basique pour vérifier que pytest fonctionne."""
        assert True

    def test_fixtures_available(self, mock_hass, mock_pool_config):
        """Vérifie que les fixtures de base sont disponibles."""
        assert mock_hass is not None
        assert mock_pool_config is not None
        assert isinstance(mock_pool_config, dict)

    def test_mock_hass_has_services(self, mock_hass):
        """Vérifie que mock_hass a les services mockés."""
        assert hasattr(mock_hass, 'services')
        assert hasattr(mock_hass.services, 'async_call')

    def test_mock_hass_has_states(self, mock_hass):
        """Vérifie que mock_hass a les états mockés."""
        assert hasattr(mock_hass, 'states')
        assert hasattr(mock_hass.states, 'get')
        assert hasattr(mock_hass.states, 'async_set')

    def test_mock_pool_config_has_required_fields(self, mock_pool_config):
        """Vérifie que la config a les champs requis."""
        required_fields = [
            "temperatureWater",
            "temperatureOutdoor",
            "leverSoleil",
            "filtration",
        ]
        for field in required_fields:
            assert field in mock_pool_config

    @pytest.mark.asyncio
    async def test_async_test_works(self):
        """Vérifie que les tests async fonctionnent."""
        # Simuler une opération async
        async def async_operation():
            return 42

        result = await async_operation()
        assert result == 42

    def test_state_factory_creates_mock_state(self, mock_state_factory):
        """Vérifie que la factory de states fonctionne."""
        state = mock_state_factory("sensor.test", "25.5")

        assert state is not None
        assert state.entity_id == "sensor.test"
        assert state.state == "25.5"

    def test_temperature_sensor_fixture(self, mock_temperature_sensor):
        """Vérifie que la fixture de température fonctionne."""
        sensor = mock_temperature_sensor(25.5)

        assert sensor is not None
        assert sensor.entity_id == "sensor.pool_temperature"
        assert sensor.state == "25.5"
        assert sensor.attributes.get("unit_of_measurement") == "°C"

    def test_setup_hass_states_helper(self, mock_hass, setup_hass_states):
        """Vérifie que le helper setup_hass_states fonctionne."""
        # Configurer plusieurs états
        setup_hass_states({
            "switch.filtration": "on",
            "sensor.temperature": "25.5",
        })

        # Vérifier qu'on peut récupérer les états
        filtration_state = mock_hass.states.get("switch.filtration")
        temp_state = mock_hass.states.get("sensor.temperature")

        assert filtration_state is not None
        assert filtration_state.state == "on"
        assert temp_state is not None
        assert temp_state.state == "25.5"

    def test_marks_available(self):
        """Vérifie que les marqueurs pytest sont disponibles."""
        # Ce test vérifie juste que pytest fonctionne avec les marks
        # Les marks sont définis dans pytest.ini
        assert True


@pytest.mark.unit
class TestPytestMarkers:
    """Vérifie que les marqueurs personnalisés fonctionnent."""

    @pytest.mark.unit
    def test_unit_marker(self):
        """Test marqué comme 'unit'."""
        assert True

    @pytest.mark.integration
    def test_integration_marker(self):
        """Test marqué comme 'integration'."""
        assert True

    @pytest.mark.bugs
    def test_bugs_marker(self):
        """Test marqué comme 'bugs' (non-régression)."""
        assert True
