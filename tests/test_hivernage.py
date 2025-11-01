"""Tests for hivernage.py module - Winter mode filtration calculations.

Tests the winter mode (hivernage) filtration logic including:
- Winter mode detection (getHivernage)
- Status display with mode (getStatusHivernage)
- Time calculation with temp/3 method and minimum
- Distribution patterns (1/2-1/2, 1/3-2/3, 2/3-1/3, 1/1-, -1/1)
- Sunrise vs fixed time pivot choice
- Frost protection (temperatureSecurite with hysteresis)
- 5-minute cycles every 3 hours (filtration5mn3h)
- Temperature tracking

Functions tested:
1. getHivernage() - Determine if in winter mode
2. getStatusHivernage() - Get status with mode suffix
3. calculateTimeFiltrationHivernage() - Calculate filtration time
4. calculateStatusFiltrationHivernage() - Determine filtration state
5. calculateTimeFiltrationWithTemperatureHivernage() - Temp/3 calculation (from utils)
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import time

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")


@pytest.fixture
def mock_hivernage_controller(mock_hass, mock_pool_config):
    """Create a mock controller with HivernageMixin."""
    from custom_components.pool_control.controller import PoolController

    controller = PoolController(mock_hass, mock_pool_config)

    # Mock status objects
    controller.filtrationTimeStatus = MagicMock()
    controller.filtrationTimeStatus.set_status = Mock()
    controller.filtrationScheduleStatus = MagicMock()
    controller.filtrationScheduleStatus.set_status = Mock()

    # Mock helper methods
    controller.updateTemperatureDisplay = Mock()
    controller.getLeverSoleil = Mock(return_value="06:30")

    # Initialize data dict
    controller.data = {}

    # Set default config values for hivernage
    controller.choixHeureFiltrationHivernage = 1  # Lever soleil
    controller.datePivotHivernage = "06:00"
    controller.distributionDatePivotHivernage = 2  # 1/3 <> 2/3
    controller.tempsDeFiltrationMinimum = 3
    controller.coefficientAjustementHivernage = 1.0
    controller.temperatureSecurite = 0
    controller.temperatureHysteresis = 0.5
    controller.filtration5mn3h = False
    controller.sondeLocalTechnique = False
    controller.sondeLocalTechniquePause = 5
    controller.disableMarcheForcee = False

    return controller


@pytest.mark.unit
class TestGetHivernage:
    """Tests for getHivernage() - Determine if in winter mode."""

    def test_returns_true_when_hivernage_active(self, mock_hivernage_controller):
        """Test that getHivernage returns True when hivernage is active."""
        mock_hivernage_controller.data["hivernageWidgetStatus"] = 1

        result = mock_hivernage_controller.getHivernage()

        assert result is True

    def test_returns_false_when_hivernage_inactive(self, mock_hivernage_controller):
        """Test that getHivernage returns False when hivernage is inactive."""
        mock_hivernage_controller.data["hivernageWidgetStatus"] = 0

        result = mock_hivernage_controller.getHivernage()

        assert result is False

    def test_returns_false_when_not_set(self, mock_hivernage_controller):
        """Test that getHivernage returns False when status is not set."""
        # No hivernageWidgetStatus in data

        result = mock_hivernage_controller.getHivernage()

        assert result is False

    def test_returns_bool_type(self, mock_hivernage_controller):
        """Test that getHivernage always returns a boolean."""
        mock_hivernage_controller.data["hivernageWidgetStatus"] = 1

        result = mock_hivernage_controller.getHivernage()

        assert isinstance(result, bool)


@pytest.mark.unit
class TestGetStatusHivernage:
    """Tests for getStatusHivernage() - Get status with mode suffix."""

    def test_adds_hivernage_suffix_when_active(self, mock_hivernage_controller):
        """Test that status gets 'Hivernage' suffix when active."""
        mock_hivernage_controller.data["hivernageWidgetStatus"] = 1

        result = mock_hivernage_controller.getStatusHivernage("Auto")

        assert result == "Auto Hivernage"

    def test_adds_saison_suffix_when_inactive(self, mock_hivernage_controller):
        """Test that status gets 'Saison' suffix when inactive."""
        mock_hivernage_controller.data["hivernageWidgetStatus"] = 0

        result = mock_hivernage_controller.getStatusHivernage("Auto")

        assert result == "Auto Saison"

    def test_handles_different_statuses(self, mock_hivernage_controller):
        """Test with different base statuses."""
        mock_hivernage_controller.data["hivernageWidgetStatus"] = 1

        test_cases = [
            ("Actif", "Actif Hivernage"),
            ("Auto", "Auto Hivernage"),
            ("Inactif", "Inactif Hivernage"),
        ]

        for base_status, expected in test_cases:
            result = mock_hivernage_controller.getStatusHivernage(base_status)
            assert result == expected


@pytest.mark.unit
class TestCalculateTimeFiltrationWithTemperatureHivernage:
    """Tests for calculateTimeFiltrationWithTemperatureHivernage() - Temp/3 calculation."""

    def test_calculates_temperature_divided_by_three(self, mock_hivernage_controller):
        """Test basic temp/3 calculation."""
        mock_hivernage_controller.coefficientAjustementHivernage = 1.0
        mock_hivernage_controller.tempsDeFiltrationMinimum = 3

        result = mock_hivernage_controller.calculateTimeFiltrationWithTemperatureHivernage(12.0)

        assert result == 4.0  # 12 / 3 = 4 hours

    def test_enforces_minimum_filtration_time(self, mock_hivernage_controller):
        """Test that minimum filtration time is enforced."""
        mock_hivernage_controller.coefficientAjustementHivernage = 1.0
        mock_hivernage_controller.tempsDeFiltrationMinimum = 3

        result = mock_hivernage_controller.calculateTimeFiltrationWithTemperatureHivernage(6.0)

        # 6 / 3 = 2 hours, but minimum is 3
        assert result == 3.0

    def test_applies_coefficient_adjustment(self, mock_hivernage_controller):
        """Test that coefficient adjustment is applied."""
        mock_hivernage_controller.coefficientAjustementHivernage = 1.5
        mock_hivernage_controller.tempsDeFiltrationMinimum = 3

        result = mock_hivernage_controller.calculateTimeFiltrationWithTemperatureHivernage(12.0)

        assert result == 6.0  # (12 / 3) * 1.5 = 6 hours

    def test_various_temperatures(self, mock_hivernage_controller):
        """Test various temperature values."""
        mock_hivernage_controller.coefficientAjustementHivernage = 1.0
        mock_hivernage_controller.tempsDeFiltrationMinimum = 3

        test_cases = [
            (3.0, 3.0),   # Below minimum
            (9.0, 3.0),   # Exactly at minimum
            (15.0, 5.0),  # Above minimum
            (18.0, 6.0),  # Above minimum
        ]

        for temp, expected in test_cases:
            result = mock_hivernage_controller.calculateTimeFiltrationWithTemperatureHivernage(temp)
            assert result == expected


@pytest.mark.unit
class TestCalculateTimeFiltrationHivernage:
    """Tests for calculateTimeFiltrationHivernage() - Calculate filtration time."""

    def test_uses_temperature_maxi_when_available(self, mock_hivernage_controller):
        """Test that temperatureMaxi is used when available."""
        mock_hivernage_controller.data["temperatureMaxi"] = 15.0
        mock_hivernage_controller.coefficientAjustementHivernage = 1.0

        with patch('time.time', return_value=datetime(2025, 12, 15, 8, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(10.0, False)

        # Should use temperatureMaxi (15) not current temp (10)
        # 15/3 = 5 hours
        call_args = mock_hivernage_controller.filtrationTimeStatus.set_status.call_args
        assert call_args[0][0] == "05:00"

    def test_uses_current_temp_when_no_maxi(self, mock_hivernage_controller):
        """Test that current temp is used when temperatureMaxi is 0."""
        mock_hivernage_controller.data["temperatureMaxi"] = 0
        mock_hivernage_controller.coefficientAjustementHivernage = 1.0

        with patch('time.time', return_value=datetime(2025, 12, 15, 8, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        # Should use current temp (12)
        # 12/3 = 4 hours
        call_args = mock_hivernage_controller.filtrationTimeStatus.set_status.call_args
        assert call_args[0][0] == "04:00"

    def test_uses_sunrise_time_when_choice_is_1(self, mock_hivernage_controller):
        """Test that sunrise time is used when choixHeureFiltrationHivernage=1."""
        mock_hivernage_controller.choixHeureFiltrationHivernage = 1
        mock_hivernage_controller.getLeverSoleil = Mock(return_value="07:15")

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        # Should call getLeverSoleil
        mock_hivernage_controller.getLeverSoleil.assert_called_once()

    def test_uses_fixed_time_when_choice_is_2(self, mock_hivernage_controller):
        """Test that fixed time is used when choixHeureFiltrationHivernage=2."""
        mock_hivernage_controller.choixHeureFiltrationHivernage = 2
        mock_hivernage_controller.datePivotHivernage = "06:00"

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        # Should not call getLeverSoleil
        mock_hivernage_controller.getLeverSoleil.assert_not_called()

    def test_distribution_pattern_half_half(self, mock_hivernage_controller):
        """Test 1/2 <> 1/2 distribution pattern."""
        mock_hivernage_controller.distributionDatePivotHivernage = 1
        mock_hivernage_controller.tempsDeFiltrationMinimum = 3

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)  # 12/3 = 4h

        # Verify times are set
        assert mock_hivernage_controller.get_data("filtrationDebut") is not None
        assert mock_hivernage_controller.get_data("filtrationFin") is not None

    def test_distribution_pattern_one_third_two_thirds(self, mock_hivernage_controller):
        """Test 1/3 <> 2/3 distribution pattern."""
        mock_hivernage_controller.distributionDatePivotHivernage = 2

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        assert mock_hivernage_controller.get_data("filtrationDebut") is not None
        assert mock_hivernage_controller.get_data("filtrationFin") is not None

    def test_distribution_pattern_two_thirds_one_third(self, mock_hivernage_controller):
        """Test 2/3 <> 1/3 distribution pattern."""
        mock_hivernage_controller.distributionDatePivotHivernage = 3

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        assert mock_hivernage_controller.get_data("filtrationDebut") is not None

    def test_distribution_pattern_all_before(self, mock_hivernage_controller):
        """Test 1/1 <> distribution pattern (all before pivot)."""
        mock_hivernage_controller.distributionDatePivotHivernage = 4

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        assert mock_hivernage_controller.get_data("filtrationDebut") is not None

    def test_distribution_pattern_all_after(self, mock_hivernage_controller):
        """Test <> 1/1 distribution pattern (all after pivot)."""
        mock_hivernage_controller.distributionDatePivotHivernage = 5

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        assert mock_hivernage_controller.get_data("filtrationDebut") is not None

    def test_tomorrow_flag_adds_one_day(self, mock_hivernage_controller):
        """Test that flgTomorrow=True adds one day to calculation."""
        mock_hivernage_controller.data["temperatureMaxi"] = 0

        # Current time after pivot
        current_time = datetime(2025, 12, 15, 8, 0).timestamp()

        with patch('time.time', return_value=current_time):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, True)

        filtration_debut = mock_hivernage_controller.get_data("filtrationDebut")

        # filtrationDebut should be tomorrow
        debut_date = datetime.fromtimestamp(filtration_debut).date()
        expected_date = datetime(2025, 12, 16).date()

        assert debut_date == expected_date

    def test_tomorrow_flag_resets_temperature_maxi(self, mock_hivernage_controller):
        """Test that flgTomorrow=True resets temperatureMaxi."""
        mock_hivernage_controller.data["temperatureMaxi"] = 15.0

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, True)

        # temperatureMaxi should be reset to 0
        assert mock_hivernage_controller.get_data("temperatureMaxi") == 0

    def test_sets_calculate_status(self, mock_hivernage_controller):
        """Test that calculateStatus is set to 1."""
        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        assert mock_hivernage_controller.get_data("calculateStatus") == 1

    def test_updates_filtration_time_status(self, mock_hivernage_controller):
        """Test that filtrationTimeStatus is updated."""
        mock_hivernage_controller.data["temperatureMaxi"] = 0

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        # Should set filtrationTimeStatus to "04:00" (12/3 = 4)
        mock_hivernage_controller.filtrationTimeStatus.set_status.assert_called_once_with("04:00")

    def test_updates_filtration_schedule_status(self, mock_hivernage_controller):
        """Test that filtrationScheduleStatus is updated with asterisk."""
        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        mock_hivernage_controller.filtrationScheduleStatus.set_status.assert_called_once()
        call_args = mock_hivernage_controller.filtrationScheduleStatus.set_status.call_args[0][0]

        # Should start with asterisk and contain temperature
        assert call_args.startswith("* ")
        assert "°C" in call_args


@pytest.mark.unit
class TestCalculateStatusFiltrationHivernage:
    """Tests for calculateStatusFiltrationHivernage() - Determine filtration state."""

    @pytest.mark.asyncio
    async def test_triggers_calculation_when_never_run(self, mock_hivernage_controller):
        """Test that calculation is triggered when filtrationDebut=0."""
        mock_hivernage_controller.data["filtrationDebut"] = 0
        mock_hivernage_controller.data["filtrationFin"] = 0

        with patch.object(mock_hivernage_controller, 'calculateTimeFiltrationHivernage') as mock_calc:
            with patch('time.time', return_value=datetime(2025, 12, 15, 8, 0).timestamp()):
                await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 5.0)

            # Should call calculateTimeFiltrationHivernage
            assert mock_calc.call_count >= 1

    @pytest.mark.asyncio
    async def test_activates_filtration_in_time_range(self, mock_hivernage_controller):
        """Test that filtration is activated when current time is in range."""
        # Set up time range: 05:00 - 09:00
        current_time = datetime(2025, 12, 15, 7, 0)  # 07:00 (in range)
        debut = datetime(2025, 12, 15, 5, 0).timestamp()
        fin = datetime(2025, 12, 15, 9, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)

        with patch('time.time', return_value=current_time.timestamp()):
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 5.0)

        # filtrationHivernage should be set to 1
        assert mock_hivernage_controller.get_data("filtrationHivernage") == 1

    @pytest.mark.asyncio
    async def test_deactivates_filtration_outside_range(self, mock_hivernage_controller):
        """Test that filtration is deactivated when outside time range."""
        # Set up time range: 05:00 - 09:00
        current_time = datetime(2025, 12, 15, 12, 0)  # 12:00 (outside)
        debut = datetime(2025, 12, 15, 5, 0).timestamp()
        fin = datetime(2025, 12, 15, 9, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["calculateStatus"] = 0

        with patch('time.time', return_value=current_time.timestamp()):
            with patch.object(mock_hivernage_controller, 'calculateTimeFiltrationHivernage'):
                await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 5.0)

        # filtrationHivernage should be 0
        filtration_hiv = mock_hivernage_controller.get_data("filtrationHivernage", 0)
        assert filtration_hiv == 0

    @pytest.mark.asyncio
    async def test_updates_temperature_display_with_probe_delay(self, mock_hivernage_controller):
        """Test that temperature display updates after probe delay."""
        mock_hivernage_controller.sondeLocalTechnique = True
        mock_hivernage_controller.sondeLocalTechniquePause = 5

        # Current time is 10 minutes after start (> 5 min delay)
        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        current_time = datetime(2025, 12, 15, 6, 10).timestamp()  # +10 min
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)

        with patch('time.time', return_value=current_time):
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(12.0, 5.0)

        # Should update temperature display
        mock_hivernage_controller.updateTemperatureDisplay.assert_called_with(12.0)

    @pytest.mark.asyncio
    async def test_tracks_temperature_maxi(self, mock_hivernage_controller):
        """Test that temperatureMaxi is tracked."""
        mock_hivernage_controller.sondeLocalTechnique = False

        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        current_time = datetime(2025, 12, 15, 7, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["temperatureMaxi"] = 10.0

        with patch('time.time', return_value=current_time):
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(12.0, 5.0)

        # temperatureMaxi should be updated to 12.0
        assert mock_hivernage_controller.get_data("temperatureMaxi") == 12.0

    @pytest.mark.asyncio
    async def test_frost_protection_activates_below_threshold(self, mock_hivernage_controller):
        """Test that frost protection activates when temperature drops below threshold."""
        mock_hivernage_controller.temperatureSecurite = 2.0
        mock_hivernage_controller.temperatureHysteresis = 0.5

        # Outside time range but temperature is cold
        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        current_time = datetime(2025, 12, 15, 12, 0).timestamp()  # Outside range
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["filtrationHivernageSecurite"] = 0

        with patch('time.time', return_value=current_time):
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 1.5)  # Outdoor < 2.0

        # Should activate frost protection
        assert mock_hivernage_controller.get_data("filtrationHivernageSecurite") == 1
        assert mock_hivernage_controller.get_data("filtrationHivernage") == 1

    @pytest.mark.asyncio
    async def test_frost_protection_deactivates_with_hysteresis(self, mock_hivernage_controller):
        """Test that frost protection deactivates with hysteresis."""
        mock_hivernage_controller.temperatureSecurite = 2.0
        mock_hivernage_controller.temperatureHysteresis = 0.5

        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        current_time = datetime(2025, 12, 15, 12, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["filtrationHivernageSecurite"] = 1  # Was active

        with patch('time.time', return_value=current_time):
            # Temperature rises above threshold + hysteresis
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 3.0)  # > 2.5

        # Should deactivate frost protection
        assert mock_hivernage_controller.get_data("filtrationHivernageSecurite") == 0

    @pytest.mark.asyncio
    async def test_frost_protection_stays_active_within_hysteresis(self, mock_hivernage_controller):
        """Test that frost protection stays active within hysteresis range."""
        mock_hivernage_controller.temperatureSecurite = 2.0
        mock_hivernage_controller.temperatureHysteresis = 0.5

        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        current_time = datetime(2025, 12, 15, 12, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["filtrationHivernageSecurite"] = 1

        with patch('time.time', return_value=current_time):
            # Temperature is above threshold but below threshold + hysteresis
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 2.3)  # 2.0 < 2.3 < 2.5

        # Should stay active
        assert mock_hivernage_controller.get_data("filtrationHivernageSecurite") == 1

    @pytest.mark.asyncio
    async def test_5min_every_3h_at_0200(self, mock_hivernage_controller):
        """Test 5-minute cycle at 02:00."""
        mock_hivernage_controller.filtration5mn3h = True

        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)

        # Time is 02:02 (in 5-minute window)
        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "0202"
            with patch('time.time', return_value=datetime(2025, 12, 15, 2, 2).timestamp()):
                await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 5.0)

        # Should activate filtration
        assert mock_hivernage_controller.get_data("filtrationHivernage") == 1

    @pytest.mark.asyncio
    async def test_5min_every_3h_all_time_slots(self, mock_hivernage_controller):
        """Test all 8 time slots for 5-minute cycles."""
        mock_hivernage_controller.filtration5mn3h = True

        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)

        # Test all 8 time slots
        time_slots = ["0202", "0502", "0802", "1102", "1402", "1702", "2002", "2302"]

        for time_slot in time_slots:
            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value.strftime.return_value = time_slot
                with patch('time.time', return_value=datetime(2025, 12, 15, 2, 2).timestamp()):
                    await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 5.0)

            # Should activate filtration for each slot
            assert mock_hivernage_controller.get_data("filtrationHivernage") == 1

    @pytest.mark.asyncio
    async def test_5min_every_3h_outside_window(self, mock_hivernage_controller):
        """Test that 5-minute cycle doesn't activate outside windows."""
        mock_hivernage_controller.filtration5mn3h = True

        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["calculateStatus"] = 0

        # Time is 02:10 (outside 5-minute window)
        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "0210"
            with patch('time.time', return_value=datetime(2025, 12, 15, 12, 0).timestamp()):
                with patch.object(mock_hivernage_controller, 'calculateTimeFiltrationHivernage'):
                    await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 5.0)

        # Should not activate (outside range and outside 5min window)
        assert mock_hivernage_controller.get_data("filtrationHivernage", 0) == 0

    @pytest.mark.asyncio
    async def test_disables_marche_forcee_when_configured(self, mock_hivernage_controller):
        """Test that marcheForcee is disabled when disableMarcheForcee=True."""
        mock_hivernage_controller.disableMarcheForcee = True

        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        current_time = datetime(2025, 12, 15, 7, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["marcheForcee"] = 1

        with patch('time.time', return_value=current_time):
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 5.0)

        # marcheForcee should be set to 0
        assert mock_hivernage_controller.get_data("marcheForcee") == 0

    @pytest.mark.asyncio
    async def test_recalculates_for_tomorrow_when_past_range(self, mock_hivernage_controller):
        """Test that calculation is triggered for tomorrow when past range."""
        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()
        current_time = datetime(2025, 12, 15, 14, 0).timestamp()  # After end

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["calculateStatus"] = 0

        with patch('time.time', return_value=current_time):
            with patch.object(mock_hivernage_controller, 'calculateTimeFiltrationHivernage') as mock_calc:
                await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 5.0)

            # Should call calculateTimeFiltrationHivernage with flgTomorrow=True
            mock_calc.assert_called_with(10.0, True)

    @pytest.mark.asyncio
    async def test_resets_filtration_temperature(self, mock_hivernage_controller):
        """Test that filtrationTemperature is reset to 0."""
        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        current_time = datetime(2025, 12, 15, 7, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["filtrationTemperature"] = 1

        with patch('time.time', return_value=current_time):
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 5.0)

        # filtrationTemperature should be set to 0
        assert mock_hivernage_controller.get_data("filtrationTemperature") == 0


@pytest.mark.integration
class TestHivernageIntegration:
    """Integration tests for hivernage mode."""

    def test_full_calculation_cycle(self, mock_hivernage_controller):
        """Test complete calculation cycle in hivernage mode."""
        mock_hivernage_controller.coefficientAjustementHivernage = 1.0
        mock_hivernage_controller.distributionDatePivotHivernage = 2
        mock_hivernage_controller.choixHeureFiltrationHivernage = 1

        with patch('time.time', return_value=datetime(2025, 12, 15, 5, 0).timestamp()):
            mock_hivernage_controller.calculateTimeFiltrationHivernage(12.0, False)

        # Verify all data is set
        assert mock_hivernage_controller.get_data("filtrationDebut") > 0
        assert mock_hivernage_controller.get_data("filtrationFin") > 0
        assert mock_hivernage_controller.get_data("calculateStatus") == 1

        # Verify UI updates
        assert mock_hivernage_controller.filtrationTimeStatus.set_status.called
        assert mock_hivernage_controller.filtrationScheduleStatus.set_status.called

    @pytest.mark.asyncio
    async def test_frost_protection_cycle(self, mock_hivernage_controller):
        """Test complete frost protection activation and deactivation cycle."""
        mock_hivernage_controller.temperatureSecurite = 2.0
        mock_hivernage_controller.temperatureHysteresis = 0.5

        # Initial state: no frost protection
        mock_hivernage_controller.data["filtrationDebut"] = 100
        mock_hivernage_controller.data["filtrationFin"] = 200

        # Step 1: Temperature drops, activate protection
        with patch('time.time', return_value=datetime(2025, 12, 15, 12, 0).timestamp()):
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 1.0)

        assert mock_hivernage_controller.get_data("filtrationHivernageSecurite") == 1

        # Step 2: Temperature rises slightly (within hysteresis), stay active
        with patch('time.time', return_value=datetime(2025, 12, 15, 12, 5).timestamp()):
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 2.3)

        assert mock_hivernage_controller.get_data("filtrationHivernageSecurite") == 1

        # Step 3: Temperature rises above threshold + hysteresis, deactivate
        with patch('time.time', return_value=datetime(2025, 12, 15, 12, 10).timestamp()):
            await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 3.0)

        assert mock_hivernage_controller.get_data("filtrationHivernageSecurite") == 0

    @pytest.mark.asyncio
    async def test_combined_filtration_and_frost_protection(self, mock_hivernage_controller):
        """Test filtration activates from either time range or frost protection."""
        mock_hivernage_controller.temperatureSecurite = 2.0
        mock_hivernage_controller.filtration5mn3h = False

        # Outside time range
        debut = datetime(2025, 12, 15, 6, 0).timestamp()
        fin = datetime(2025, 12, 15, 10, 0).timestamp()
        current_time = datetime(2025, 12, 15, 12, 0).timestamp()

        mock_hivernage_controller.data["filtrationDebut"] = int(debut)
        mock_hivernage_controller.data["filtrationFin"] = int(fin)
        mock_hivernage_controller.data["calculateStatus"] = 0

        with patch('time.time', return_value=current_time):
            with patch.object(mock_hivernage_controller, 'calculateTimeFiltrationHivernage'):
                # Cold temperature triggers frost protection
                await mock_hivernage_controller.calculateStatusFiltrationHivernage(10.0, 1.0)

        # Should activate due to frost protection even though outside time range
        assert mock_hivernage_controller.get_data("filtrationHivernage") == 1
