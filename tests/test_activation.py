"""Tests for activation.py module.

Tests the 13 functions of ActivationMixin that control pool device activation logic.
These functions were refactored in PR #4 to reduce complexity and improve maintainability.

Functions tested:
1. activatingDevices() - Main entry point
2. _update_status_display() - Update UI status
3. _handle_active_mode() - Dispatcher for active mode
4. _handle_normal_filtration_mode() - Normal filtration mode
5. _should_activate_filtration() - Decision for filtration activation
6. _activate_filtration_system() - Activate filtration sequence
7. _should_activate_treatment() - Decision for treatment activation
8. _activate_treatment() - Activate treatment
9. _deactivate_filtration_system() - Deactivate filtration sequence
10. _deactivate_treatment() - Deactivate treatment
11. _handle_lavage_stop_mode() - Lavage stop mode
12. _handle_lavage_filtration_mode() - Lavage filtration mode
13. _handle_stop_all() - Total stop mode
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import asyncio

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")

from custom_components.pool_control.activation import DEVICE_ACTIVATION_DELAY


@pytest.fixture
def mock_controller(mock_hass, mock_pool_config):
    """Create a mock controller with ActivationMixin."""
    from custom_components.pool_control.controller import PoolController

    controller = PoolController(mock_hass, mock_pool_config)

    # Mock all the methods that will be called
    controller.filtrationOn = AsyncMock()
    controller.filtrationStop = AsyncMock()
    controller.traitementOn = AsyncMock()
    controller.traitementStop = AsyncMock()
    controller.traitement_2_On = AsyncMock()
    controller.traitement_2_Stop = AsyncMock()
    controller.surpresseurOn = AsyncMock()
    controller.surpresseurStop = AsyncMock()
    controller.getStateTraitement = Mock(return_value=False)
    controller.getStateTraitement_2 = Mock(return_value=False)
    controller.getStateSurpresseur = Mock(return_value=False)
    controller.getStatusHivernage = Mock(side_effect=lambda x: x)

    # Mock asservissementStatus
    controller.asservissementStatus = MagicMock()
    controller.asservissementStatus.set_status = Mock()

    # Initialize data dict
    controller.data = {}

    return controller


@pytest.mark.unit
class TestActivatingDevices:
    """Tests for activatingDevices() - Main entry point."""

    @pytest.mark.asyncio
    async def test_activating_devices_calls_update_status(self, mock_controller):
        """Test that activatingDevices calls _update_status_display."""
        with patch.object(mock_controller, '_update_status_display') as mock_update:
            with patch.object(mock_controller, '_handle_active_mode', new=AsyncMock()):
                await mock_controller.activatingDevices()
                mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_activating_devices_normal_mode(self, mock_controller):
        """Test activatingDevices in normal mode (not arretTotal)."""
        mock_controller.data["arretTotal"] = 0

        with patch.object(mock_controller, '_handle_active_mode', new=AsyncMock()) as mock_active:
            with patch.object(mock_controller, '_handle_stop_all', new=AsyncMock()) as mock_stop:
                await mock_controller.activatingDevices()

                mock_active.assert_called_once()
                mock_stop.assert_not_called()

    @pytest.mark.asyncio
    async def test_activating_devices_stop_mode(self, mock_controller):
        """Test activatingDevices in total stop mode (arretTotal=1)."""
        mock_controller.data["arretTotal"] = 1

        with patch.object(mock_controller, '_handle_active_mode', new=AsyncMock()) as mock_active:
            with patch.object(mock_controller, '_handle_stop_all', new=AsyncMock()) as mock_stop:
                await mock_controller.activatingDevices()

                mock_stop.assert_called_once()
                mock_active.assert_not_called()


@pytest.mark.unit
class TestUpdateStatusDisplay:
    """Tests for _update_status_display() - Update UI status."""

    def test_update_status_display_actif(self, mock_controller):
        """Test status display shows 'Actif' when marcheForcee=1."""
        mock_controller.data["arretTotal"] = 0
        mock_controller.data["marcheForcee"] = 1

        mock_controller._update_status_display()

        mock_controller.asservissementStatus.set_status.assert_called_once_with("Actif")

    def test_update_status_display_auto(self, mock_controller):
        """Test status display shows 'Auto' when marcheForcee=0."""
        mock_controller.data["arretTotal"] = 0
        mock_controller.data["marcheForcee"] = 0

        mock_controller._update_status_display()

        mock_controller.asservissementStatus.set_status.assert_called_once_with("Auto")

    def test_update_status_display_inactif(self, mock_controller):
        """Test status display shows 'Inactif' when arretTotal=1."""
        mock_controller.data["arretTotal"] = 1

        mock_controller._update_status_display()

        mock_controller.asservissementStatus.set_status.assert_called_once_with("Inactif")

    def test_update_status_display_with_hivernage_modification(self, mock_controller):
        """Test status is modified by getStatusHivernage."""
        mock_controller.data["arretTotal"] = 0
        mock_controller.data["marcheForcee"] = 0
        mock_controller.getStatusHivernage = Mock(return_value="Auto / Hivernage")

        mock_controller._update_status_display()

        mock_controller.getStatusHivernage.assert_called_once_with("Auto")
        mock_controller.asservissementStatus.set_status.assert_called_once_with("Auto / Hivernage")


@pytest.mark.unit
class TestHandleActiveMode:
    """Tests for _handle_active_mode() - Dispatcher for active mode."""

    @pytest.mark.asyncio
    async def test_handle_active_mode_normal_filtration(self, mock_controller):
        """Test active mode with filtrationLavage=0 (normal)."""
        mock_controller.data["filtrationLavage"] = 0

        with patch.object(mock_controller, '_handle_normal_filtration_mode', new=AsyncMock()) as mock_normal:
            await mock_controller._handle_active_mode()
            mock_normal.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_active_mode_lavage_stop(self, mock_controller):
        """Test active mode with filtrationLavage=1 (lavage stop)."""
        mock_controller.data["filtrationLavage"] = 1

        with patch.object(mock_controller, '_handle_lavage_stop_mode', new=AsyncMock()) as mock_stop:
            await mock_controller._handle_active_mode()
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_active_mode_lavage_filtration(self, mock_controller):
        """Test active mode with filtrationLavage=2 (lavage filtration)."""
        mock_controller.data["filtrationLavage"] = 2

        with patch.object(mock_controller, '_handle_lavage_filtration_mode', new=AsyncMock()) as mock_filt:
            await mock_controller._handle_active_mode()
            mock_filt.assert_called_once()


@pytest.mark.unit
class TestHandleNormalFiltrationMode:
    """Tests for _handle_normal_filtration_mode() - Normal filtration mode."""

    @pytest.mark.asyncio
    async def test_normal_filtration_activates_when_should(self, mock_controller):
        """Test normal filtration activates when _should_activate_filtration returns True."""
        with patch.object(mock_controller, '_should_activate_filtration', return_value=True):
            with patch.object(mock_controller, '_activate_filtration_system', new=AsyncMock()) as mock_activate:
                await mock_controller._handle_normal_filtration_mode()
                mock_activate.assert_called_once()

    @pytest.mark.asyncio
    async def test_normal_filtration_deactivates_when_should_not(self, mock_controller):
        """Test normal filtration deactivates when _should_activate_filtration returns False."""
        with patch.object(mock_controller, '_should_activate_filtration', return_value=False):
            with patch.object(mock_controller, '_deactivate_filtration_system', new=AsyncMock()) as mock_deactivate:
                await mock_controller._handle_normal_filtration_mode()
                mock_deactivate.assert_called_once()


@pytest.mark.unit
class TestShouldActivateFiltration:
    """Tests for _should_activate_filtration() - Decision for filtration activation."""

    def test_should_activate_when_filtration_temperature(self, mock_controller):
        """Test activation when filtrationTemperature=1."""
        mock_controller.data["filtrationTemperature"] = 1
        assert mock_controller._should_activate_filtration() is True

    def test_should_activate_when_filtration_solaire(self, mock_controller):
        """Test activation when filtrationSolaire=1."""
        mock_controller.data["filtrationSolaire"] = 1
        assert mock_controller._should_activate_filtration() is True

    def test_should_activate_when_filtration_hivernage(self, mock_controller):
        """Test activation when filtrationHivernage=1."""
        mock_controller.data["filtrationHivernage"] = 1
        assert mock_controller._should_activate_filtration() is True

    def test_should_activate_when_filtration_surpresseur(self, mock_controller):
        """Test activation when filtrationSurpresseur=1."""
        mock_controller.data["filtrationSurpresseur"] = 1
        assert mock_controller._should_activate_filtration() is True

    def test_should_activate_when_marche_forcee(self, mock_controller):
        """Test activation when marcheForcee=1."""
        mock_controller.data["marcheForcee"] = 1
        assert mock_controller._should_activate_filtration() is True

    def test_should_not_activate_when_all_false(self, mock_controller):
        """Test no activation when all conditions are false."""
        mock_controller.data["filtrationTemperature"] = 0
        mock_controller.data["filtrationSolaire"] = 0
        mock_controller.data["filtrationHivernage"] = 0
        mock_controller.data["filtrationSurpresseur"] = 0
        mock_controller.data["marcheForcee"] = 0
        assert mock_controller._should_activate_filtration() is False

    def test_should_activate_returns_bool(self, mock_controller):
        """Test that _should_activate_filtration returns a bool."""
        result = mock_controller._should_activate_filtration()
        assert isinstance(result, bool)


@pytest.mark.unit
class TestActivateFiltrationSystem:
    """Tests for _activate_filtration_system() - Activate filtration sequence."""

    @pytest.mark.asyncio
    async def test_activate_filtration_system_basic(self, mock_controller):
        """Test basic filtration activation."""
        with patch.object(mock_controller, '_should_activate_treatment', return_value=False):
            mock_controller.data["filtrationSurpresseur"] = 0

            await mock_controller._activate_filtration_system()

            mock_controller.filtrationOn.assert_called_once()
            mock_controller.surpresseurStop.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_filtration_with_treatment(self, mock_controller):
        """Test filtration activation with treatment."""
        with patch.object(mock_controller, '_should_activate_treatment', return_value=True):
            with patch.object(mock_controller, '_activate_treatment', new=AsyncMock()) as mock_treat:
                mock_controller.data["filtrationSurpresseur"] = 0

                await mock_controller._activate_filtration_system()

                mock_controller.filtrationOn.assert_called_once()
                mock_treat.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_filtration_with_surpresseur(self, mock_controller):
        """Test filtration activation with surpresseur."""
        with patch.object(mock_controller, '_should_activate_treatment', return_value=False):
            with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
                mock_controller.data["filtrationSurpresseur"] = 1

                await mock_controller._activate_filtration_system()

                mock_controller.filtrationOn.assert_called_once()
                mock_sleep.assert_called_once_with(DEVICE_ACTIVATION_DELAY)
                mock_controller.surpresseurOn.assert_called_once()


@pytest.mark.unit
class TestShouldActivateTreatment:
    """Tests for _should_activate_treatment() - Decision for treatment activation."""

    def test_should_activate_when_filtration_temperature(self, mock_controller):
        """Test treatment activation when filtrationTemperature=1."""
        mock_controller.data["filtrationTemperature"] = 1
        assert mock_controller._should_activate_treatment() is True

    def test_should_activate_when_hivernage_and_treatment_enabled(self, mock_controller):
        """Test treatment activation in hivernage when traitementHivernage=True."""
        mock_controller.data["filtrationTemperature"] = 0
        mock_controller.data["filtrationHivernage"] = 1
        mock_controller.traitementHivernage = True
        assert mock_controller._should_activate_treatment() is True

    def test_should_not_activate_when_hivernage_and_treatment_disabled(self, mock_controller):
        """Test treatment not activated in hivernage when traitementHivernage=False."""
        mock_controller.data["filtrationTemperature"] = 0
        mock_controller.data["filtrationHivernage"] = 1
        mock_controller.traitementHivernage = False
        assert mock_controller._should_activate_treatment() is False

    def test_should_not_activate_when_all_conditions_false(self, mock_controller):
        """Test treatment not activated when no conditions are met."""
        mock_controller.data["filtrationTemperature"] = 0
        mock_controller.data["filtrationHivernage"] = 0
        assert mock_controller._should_activate_treatment() is False

    def test_should_activate_returns_bool(self, mock_controller):
        """Test that _should_activate_treatment returns a bool."""
        result = mock_controller._should_activate_treatment()
        assert isinstance(result, bool)


@pytest.mark.unit
class TestActivateTreatment:
    """Tests for _activate_treatment() - Activate treatment."""

    @pytest.mark.asyncio
    async def test_activate_treatment_with_traitement(self, mock_controller):
        """Test treatment activation with traitement device."""
        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            mock_controller.traitement = "switch.traitement"
            mock_controller.traitement_2 = None

            await mock_controller._activate_treatment()

            mock_sleep.assert_called_once_with(DEVICE_ACTIVATION_DELAY)
            mock_controller.traitementOn.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_treatment_with_traitement_2(self, mock_controller):
        """Test treatment activation with traitement_2 device."""
        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            mock_controller.traitement = None
            mock_controller.traitement_2 = "switch.traitement_2"

            await mock_controller._activate_treatment()

            mock_sleep.assert_called_once_with(DEVICE_ACTIVATION_DELAY)
            mock_controller.traitement_2_On.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_treatment_with_both(self, mock_controller):
        """Test treatment activation with both traitement devices."""
        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            mock_controller.traitement = "switch.traitement"
            mock_controller.traitement_2 = "switch.traitement_2"

            await mock_controller._activate_treatment()

            mock_sleep.assert_called_once_with(DEVICE_ACTIVATION_DELAY)
            mock_controller.traitementOn.assert_called_once()
            mock_controller.traitement_2_On.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_treatment_with_none(self, mock_controller):
        """Test treatment activation when no devices configured."""
        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            mock_controller.traitement = None
            mock_controller.traitement_2 = None

            await mock_controller._activate_treatment()

            # Should not crash, should not sleep
            mock_sleep.assert_not_called()


@pytest.mark.unit
class TestDeactivateFiltrationSystem:
    """Tests for _deactivate_filtration_system() - Deactivate filtration sequence."""

    @pytest.mark.asyncio
    async def test_deactivate_filtration_system_basic(self, mock_controller):
        """Test basic filtration deactivation."""
        with patch.object(mock_controller, '_deactivate_treatment', new=AsyncMock()) as mock_deact_treat:
            mock_controller.getStateSurpresseur = Mock(return_value=False)

            await mock_controller._deactivate_filtration_system()

            mock_deact_treat.assert_called_once()
            mock_controller.filtrationStop.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_filtration_with_surpresseur_running(self, mock_controller):
        """Test filtration deactivation when surpresseur is running."""
        with patch.object(mock_controller, '_deactivate_treatment', new=AsyncMock()):
            with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
                mock_controller.getStateSurpresseur = Mock(return_value=True)

                await mock_controller._deactivate_filtration_system()

                mock_controller.surpresseurStop.assert_called_once()
                mock_sleep.assert_called_once_with(DEVICE_ACTIVATION_DELAY)
                mock_controller.filtrationStop.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_filtration_order(self, mock_controller):
        """Test that deactivation happens in correct order (treatment, surpresseur, filtration)."""
        call_order = []

        async def track_deactivate_treatment():
            call_order.append("treatment")

        async def track_surpresseur_stop():
            call_order.append("surpresseur")

        async def track_filtration_stop():
            call_order.append("filtration")

        with patch.object(mock_controller, '_deactivate_treatment', side_effect=track_deactivate_treatment):
            with patch('asyncio.sleep', new=AsyncMock()):
                mock_controller.getStateSurpresseur = Mock(return_value=True)
                mock_controller.surpresseurStop = AsyncMock(side_effect=track_surpresseur_stop)
                mock_controller.filtrationStop = AsyncMock(side_effect=track_filtration_stop)

                await mock_controller._deactivate_filtration_system()

                assert call_order == ["treatment", "surpresseur", "filtration"]


@pytest.mark.unit
class TestDeactivateTreatment:
    """Tests for _deactivate_treatment() - Deactivate treatment."""

    @pytest.mark.asyncio
    async def test_deactivate_treatment_with_traitement_on(self, mock_controller):
        """Test treatment deactivation when traitement is on."""
        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            mock_controller.traitement = "switch.traitement"
            mock_controller.traitement_2 = None
            mock_controller.getStateTraitement = Mock(return_value=True)

            await mock_controller._deactivate_treatment()

            mock_controller.traitementStop.assert_called_once()
            mock_sleep.assert_called_once_with(DEVICE_ACTIVATION_DELAY)

    @pytest.mark.asyncio
    async def test_deactivate_treatment_with_traitement_off(self, mock_controller):
        """Test treatment deactivation when traitement is already off."""
        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            mock_controller.traitement = "switch.traitement"
            mock_controller.traitement_2 = None
            mock_controller.getStateTraitement = Mock(return_value=False)

            await mock_controller._deactivate_treatment()

            mock_controller.traitementStop.assert_not_called()
            mock_sleep.assert_called_once_with(DEVICE_ACTIVATION_DELAY)

    @pytest.mark.asyncio
    async def test_deactivate_treatment_with_both_on(self, mock_controller):
        """Test treatment deactivation when both devices are on."""
        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            mock_controller.traitement = "switch.traitement"
            mock_controller.traitement_2 = "switch.traitement_2"
            mock_controller.getStateTraitement = Mock(return_value=True)
            mock_controller.getStateTraitement_2 = Mock(return_value=True)

            await mock_controller._deactivate_treatment()

            mock_controller.traitementStop.assert_called_once()
            mock_controller.traitement_2_Stop.assert_called_once()
            mock_sleep.assert_called_once_with(DEVICE_ACTIVATION_DELAY)

    @pytest.mark.asyncio
    async def test_deactivate_treatment_with_none(self, mock_controller):
        """Test treatment deactivation when no devices configured."""
        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            mock_controller.traitement = None
            mock_controller.traitement_2 = None

            await mock_controller._deactivate_treatment()

            # Should not crash, should not sleep
            mock_sleep.assert_not_called()


@pytest.mark.unit
class TestHandleLavageStopMode:
    """Tests for _handle_lavage_stop_mode() - Lavage stop mode."""

    @pytest.mark.asyncio
    async def test_lavage_stop_mode_stops_all(self, mock_controller):
        """Test that lavage stop mode stops all devices."""
        mock_controller.traitement = "switch.traitement"
        mock_controller.traitement_2 = "switch.traitement_2"

        await mock_controller._handle_lavage_stop_mode()

        mock_controller.traitementStop.assert_called_once()
        mock_controller.traitement_2_Stop.assert_called_once()
        mock_controller.surpresseurStop.assert_called_once()
        mock_controller.filtrationStop.assert_called_once()

    @pytest.mark.asyncio
    async def test_lavage_stop_mode_with_no_traitement(self, mock_controller):
        """Test lavage stop mode when no traitement devices configured."""
        mock_controller.traitement = None
        mock_controller.traitement_2 = None

        await mock_controller._handle_lavage_stop_mode()

        # Should not crash
        mock_controller.surpresseurStop.assert_called_once()
        mock_controller.filtrationStop.assert_called_once()


@pytest.mark.unit
class TestHandleLavageFiltrationMode:
    """Tests for _handle_lavage_filtration_mode() - Lavage filtration mode."""

    @pytest.mark.asyncio
    async def test_lavage_filtration_mode_stops_treatment_starts_filtration(self, mock_controller):
        """Test that lavage filtration mode stops treatment and starts filtration."""
        mock_controller.traitement = "switch.traitement"
        mock_controller.traitement_2 = "switch.traitement_2"

        await mock_controller._handle_lavage_filtration_mode()

        mock_controller.traitementStop.assert_called_once()
        mock_controller.traitement_2_Stop.assert_called_once()
        mock_controller.surpresseurStop.assert_called_once()
        mock_controller.filtrationOn.assert_called_once()

    @pytest.mark.asyncio
    async def test_lavage_filtration_mode_with_no_traitement(self, mock_controller):
        """Test lavage filtration mode when no traitement devices configured."""
        mock_controller.traitement = None
        mock_controller.traitement_2 = None

        await mock_controller._handle_lavage_filtration_mode()

        # Should not crash
        mock_controller.surpresseurStop.assert_called_once()
        mock_controller.filtrationOn.assert_called_once()


@pytest.mark.unit
class TestHandleStopAll:
    """Tests for _handle_stop_all() - Total stop mode."""

    @pytest.mark.asyncio
    async def test_stop_all_stops_all_devices(self, mock_controller):
        """Test that stop all mode stops all devices."""
        mock_controller.traitement = "switch.traitement"
        mock_controller.traitement_2 = "switch.traitement_2"

        await mock_controller._handle_stop_all()

        mock_controller.traitementStop.assert_called_once()
        mock_controller.traitement_2_Stop.assert_called_once()
        mock_controller.surpresseurStop.assert_called_once()
        mock_controller.filtrationStop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_all_with_no_traitement(self, mock_controller):
        """Test stop all mode when no traitement devices configured."""
        mock_controller.traitement = None
        mock_controller.traitement_2 = None

        await mock_controller._handle_stop_all()

        # Should not crash
        mock_controller.surpresseurStop.assert_called_once()
        mock_controller.filtrationStop.assert_called_once()


@pytest.mark.unit
class TestActivationIntegration:
    """Integration tests for activation flow."""

    @pytest.mark.asyncio
    async def test_full_activation_flow_temperature_mode(self, mock_controller):
        """Test complete activation flow in temperature mode."""
        with patch('asyncio.sleep', new=AsyncMock()):
            # Setup: temperature mode, no surpresseur, no lavage
            mock_controller.data["arretTotal"] = 0
            mock_controller.data["marcheForcee"] = 0
            mock_controller.data["filtrationLavage"] = 0
            mock_controller.data["filtrationTemperature"] = 1
            mock_controller.data["filtrationSolaire"] = 0
            mock_controller.data["filtrationHivernage"] = 0
            mock_controller.data["filtrationSurpresseur"] = 0
            mock_controller.traitement = "switch.traitement"
            mock_controller.traitement_2 = None

            await mock_controller.activatingDevices()

            # Verify correct calls
            mock_controller.filtrationOn.assert_called_once()
            mock_controller.traitementOn.assert_called_once()
            mock_controller.surpresseurStop.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_deactivation_flow(self, mock_controller):
        """Test complete deactivation flow."""
        with patch('asyncio.sleep', new=AsyncMock()):
            # Setup: all off
            mock_controller.data["arretTotal"] = 0
            mock_controller.data["filtrationLavage"] = 0
            mock_controller.data["filtrationTemperature"] = 0
            mock_controller.data["filtrationSolaire"] = 0
            mock_controller.data["filtrationHivernage"] = 0
            mock_controller.data["filtrationSurpresseur"] = 0
            mock_controller.data["marcheForcee"] = 0
            mock_controller.traitement = "switch.traitement"
            mock_controller.getStateTraitement = Mock(return_value=True)
            mock_controller.getStateSurpresseur = Mock(return_value=False)

            await mock_controller.activatingDevices()

            # Verify correct calls
            mock_controller.traitementStop.assert_called_once()
            mock_controller.filtrationStop.assert_called_once()

    @pytest.mark.asyncio
    async def test_activation_with_lavage_mode(self, mock_controller):
        """Test activation in lavage mode."""
        # Setup: lavage stop mode
        mock_controller.data["arretTotal"] = 0
        mock_controller.data["filtrationLavage"] = 1
        mock_controller.traitement = "switch.traitement"

        await mock_controller.activatingDevices()

        # Verify lavage stop behavior
        mock_controller.traitementStop.assert_called_once()
        mock_controller.filtrationStop.assert_called_once()
        mock_controller.surpresseurStop.assert_called_once()
