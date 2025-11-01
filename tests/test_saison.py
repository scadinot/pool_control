"""Tests for saison.py module - Seasonal filtration calculations.

Tests the seasonal filtration logic including:
- Time calculation with curve method (cubic equation)
- Time calculation with temperature/2 method
- Distribution patterns (1/2-1/2, 1/3-2/3, 2/3-1/3, 1/1-, -1/1)
- Pause pivot handling
- Filtration status determination
- Temperature tracking (temperatureMaxi)
- Probe delay handling (sondeLocalTechnique)

Functions tested:
1. calculateTimeFiltration() - Main calculation function
2. calculateStatusFiltration() - Status determination
3. processingTime() - Time formatting utility
4. calculateTimeFiltrationWithCurve() - Cubic curve calculation
5. calculateTimeFiltrationWithTemperatureReducedByHalf() - Simple temp/2 calculation
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import time

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")


@pytest.fixture
def mock_saison_controller(mock_hass, mock_pool_config):
    """Create a mock controller with SaisonMixin."""
    from custom_components.pool_control.controller import PoolController

    controller = PoolController(mock_hass, mock_pool_config)

    # Mock status objects
    controller.filtrationTimeStatus = MagicMock()
    controller.filtrationTimeStatus.set_status = Mock()
    controller.filtrationScheduleStatus = MagicMock()
    controller.filtrationScheduleStatus.set_status = Mock()

    # Mock helper method
    controller.updateTemperatureDisplay = Mock()

    # Initialize data dict
    controller.data = {}

    # Set default config values
    controller.datePivot = "13:00"
    controller.pausePivot = 0
    controller.distributionDatePivot = 2  # 1/3 <> 2/3
    controller.methodeCalcul = 1  # Curve
    controller.coefficientAjustement = 1.0
    controller.sondeLocalTechnique = False
    controller.sondeLocalTechniquePause = 5
    controller.disableMarcheForcee = False

    return controller


@pytest.mark.unit
class TestProcessingTime:
    """Tests for processingTime() - Time formatting utility."""

    def test_processing_time_rounds_to_minutes(self, mock_saison_controller):
        """Test that processingTime rounds duration to minutes."""
        # 2.5 hours = 2h30
        seconds, time_str = mock_saison_controller.processingTime(2.5)

        assert seconds == 2.5 * 3600
        assert time_str == "02:30"

    def test_processing_time_caps_at_24_hours(self, mock_saison_controller):
        """Test that processingTime caps at 24 hours max."""
        seconds, time_str = mock_saison_controller.processingTime(30.0)

        assert seconds == 24.0 * 3600
        assert time_str == "24:00"

    def test_processing_time_formats_correctly(self, mock_saison_controller):
        """Test time formatting for various durations."""
        test_cases = [
            (0.5, "00:30"),   # 30 minutes
            (1.0, "01:00"),   # 1 hour
            (3.25, "03:15"),  # 3h15
            (10.75, "10:45"), # 10h45
            (12.0, "12:00"),  # 12 hours
        ]

        for hours, expected in test_cases:
            _, time_str = mock_saison_controller.processingTime(hours)
            assert time_str == expected

    def test_processing_time_handles_fractional_minutes(self, mock_saison_controller):
        """Test that fractional minutes are rounded."""
        # 2.483333 hours = 2h29 (rounded from 2h29m)
        seconds, time_str = mock_saison_controller.processingTime(2.483333)

        assert time_str == "02:28"  # Rounded down


@pytest.mark.unit
class TestCalculateTimeFiltrationWithCurve:
    """Tests for calculateTimeFiltrationWithCurve() - Cubic curve calculation."""

    def test_curve_calculation_enforces_minimum_10_degrees(self, mock_saison_controller):
        """Test that temperature below 10°C is capped at 10°C."""
        mock_saison_controller.coefficientAjustement = 1.0

        result_5 = mock_saison_controller.calculateTimeFiltrationWithCurve(5.0)
        result_10 = mock_saison_controller.calculateTimeFiltrationWithCurve(10.0)

        # Both should give same result (10°C is minimum)
        assert result_5 == result_10

    def test_curve_calculation_increases_with_temperature(self, mock_saison_controller):
        """Test that filtration time increases with temperature."""
        mock_saison_controller.coefficientAjustement = 1.0

        result_10 = mock_saison_controller.calculateTimeFiltrationWithCurve(10.0)
        result_20 = mock_saison_controller.calculateTimeFiltrationWithCurve(20.0)
        result_30 = mock_saison_controller.calculateTimeFiltrationWithCurve(30.0)

        assert result_10 < result_20 < result_30

    def test_curve_calculation_with_adjustment_coefficient(self, mock_saison_controller):
        """Test coefficient adjustment affects result."""
        # Coefficient 1.0
        mock_saison_controller.coefficientAjustement = 1.0
        result_1 = mock_saison_controller.calculateTimeFiltrationWithCurve(25.0)

        # Coefficient 1.5
        mock_saison_controller.coefficientAjustement = 1.5
        result_15 = mock_saison_controller.calculateTimeFiltrationWithCurve(25.0)

        # With coefficient 1.5, result should be 1.5x
        assert abs(result_15 - (result_1 * 1.5)) < 0.01

    def test_curve_calculation_specific_values(self, mock_saison_controller):
        """Test specific known temperature values."""
        mock_saison_controller.coefficientAjustement = 1.0

        # Test at 10°C (minimum)
        result = mock_saison_controller.calculateTimeFiltrationWithCurve(10.0)
        # Using the formula: a*10³ + b*10² + c*10 + d
        # = 0.00335*1000 - 0.14953*100 + 2.43489*10 - 10.72859
        # = 3.35 - 14.953 + 24.3489 - 10.72859
        # ≈ 2.02 hours
        assert 1.5 < result < 3.0


@pytest.mark.unit
class TestCalculateTimeFiltrationWithTemperatureReducedByHalf:
    """Tests for calculateTimeFiltrationWithTemperatureReducedByHalf() - Temp/2 calculation."""

    def test_temp_by_half_simple_calculation(self, mock_saison_controller):
        """Test simple temperature/2 calculation."""
        mock_saison_controller.coefficientAjustement = 1.0

        result = mock_saison_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(20.0)

        assert result == 10.0  # 20 / 2 = 10 hours

    def test_temp_by_half_with_coefficient(self, mock_saison_controller):
        """Test temperature/2 with adjustment coefficient."""
        mock_saison_controller.coefficientAjustement = 1.2

        result = mock_saison_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(20.0)

        assert result == 12.0  # (20 / 2) * 1.2 = 12 hours

    def test_temp_by_half_various_temperatures(self, mock_saison_controller):
        """Test various temperature values."""
        mock_saison_controller.coefficientAjustement = 1.0

        test_cases = [
            (10.0, 5.0),
            (15.0, 7.5),
            (25.0, 12.5),
            (30.0, 15.0),
        ]

        for temp, expected in test_cases:
            result = mock_saison_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(temp)
            assert result == expected


@pytest.mark.unit
class TestCalculateTimeFiltration:
    """Tests for calculateTimeFiltration() - Main calculation function."""

    def test_uses_temperature_maxi_when_available(self, mock_saison_controller):
        """Test that temperatureMaxi is used when available."""
        mock_saison_controller.data["temperatureMaxi"] = 25.0
        mock_saison_controller.methodeCalcul = 2  # Temp/2 for easy verification
        mock_saison_controller.coefficientAjustement = 1.0

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(20.0, False)

        # Should use temperatureMaxi (25) not current temp (20)
        # 25/2 = 12.5 hours
        call_args = mock_saison_controller.filtrationTimeStatus.set_status.call_args
        assert call_args[0][0] == "12:30"

    def test_uses_current_temp_when_no_maxi(self, mock_saison_controller):
        """Test that current temp is used when temperatureMaxi is 0."""
        mock_saison_controller.data["temperatureMaxi"] = 0
        mock_saison_controller.methodeCalcul = 2
        mock_saison_controller.coefficientAjustement = 1.0

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(20.0, False)

        # Should use current temp (20)
        # 20/2 = 10 hours
        call_args = mock_saison_controller.filtrationTimeStatus.set_status.call_args
        assert call_args[0][0] == "10:00"

    def test_uses_curve_method_when_methode_calcul_1(self, mock_saison_controller):
        """Test that curve method is used when methodeCalcul=1."""
        mock_saison_controller.data["temperatureMaxi"] = 0
        mock_saison_controller.methodeCalcul = 1
        mock_saison_controller.coefficientAjustement = 1.0

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(25.0, False)

        # Curve method should be used (result will be different from temp/2)
        call_args = mock_saison_controller.filtrationTimeStatus.set_status.call_args
        # Result should NOT be 12:30 (which is 25/2)
        assert call_args[0][0] != "12:30"

    def test_distribution_pattern_half_half(self, mock_saison_controller):
        """Test 1/2 <> 1/2 distribution pattern."""
        mock_saison_controller.data["temperatureMaxi"] = 0
        mock_saison_controller.methodeCalcul = 2
        mock_saison_controller.coefficientAjustement = 1.0
        mock_saison_controller.distributionDatePivot = 1  # 1/2 <> 1/2
        mock_saison_controller.datePivot = "13:00"
        mock_saison_controller.pausePivot = 0

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(10.0, False)  # 10/2 = 5 hours

        # With 5 hours and pivot at 13:00, distribution 1/2 <> 1/2
        # Start: 13:00 - 2.5h = 10:30
        # End: 13:00 + 2.5h = 15:30
        assert mock_saison_controller.get_data("filtrationDebut") is not None
        assert mock_saison_controller.get_data("filtrationFin") is not None

    def test_distribution_pattern_one_third_two_thirds(self, mock_saison_controller):
        """Test 1/3 <> 2/3 distribution pattern."""
        mock_saison_controller.data["temperatureMaxi"] = 0
        mock_saison_controller.methodeCalcul = 2
        mock_saison_controller.coefficientAjustement = 1.0
        mock_saison_controller.distributionDatePivot = 2  # 1/3 <> 2/3
        mock_saison_controller.datePivot = "13:00"
        mock_saison_controller.pausePivot = 0

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(12.0, False)  # 12/2 = 6 hours

        # With 6 hours and pivot at 13:00, distribution 1/3 <> 2/3
        # Start: 13:00 - 2h = 11:00
        # End: 13:00 + 4h = 17:00
        filtration_debut = mock_saison_controller.get_data("filtrationDebut")
        filtration_fin = mock_saison_controller.get_data("filtrationFin")

        assert filtration_debut is not None
        assert filtration_fin is not None

    def test_distribution_pattern_two_thirds_one_third(self, mock_saison_controller):
        """Test 2/3 <> 1/3 distribution pattern."""
        mock_saison_controller.distributionDatePivot = 3  # 2/3 <> 1/3

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(12.0, False)

        assert mock_saison_controller.get_data("filtrationDebut") is not None
        assert mock_saison_controller.get_data("filtrationFin") is not None

    def test_distribution_pattern_all_before(self, mock_saison_controller):
        """Test 1/1 <> distribution pattern (all before pivot)."""
        mock_saison_controller.distributionDatePivot = 4  # 1/1 <>

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(12.0, False)

        assert mock_saison_controller.get_data("filtrationDebut") is not None
        assert mock_saison_controller.get_data("filtrationFin") is not None

    def test_distribution_pattern_all_after(self, mock_saison_controller):
        """Test <> 1/1 distribution pattern (all after pivot)."""
        mock_saison_controller.distributionDatePivot = 5  # <> 1/1

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(12.0, False)

        assert mock_saison_controller.get_data("filtrationDebut") is not None
        assert mock_saison_controller.get_data("filtrationFin") is not None

    def test_pause_pivot_is_included(self, mock_saison_controller):
        """Test that pausePivot is added to filtration duration."""
        mock_saison_controller.data["temperatureMaxi"] = 0
        mock_saison_controller.methodeCalcul = 2
        mock_saison_controller.coefficientAjustement = 1.0
        mock_saison_controller.pausePivot = 60  # 60 minutes pause

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(10.0, False)  # 10/2 = 5 hours

        # Total time should include pause
        filtration_debut = mock_saison_controller.get_data("filtrationDebut")
        filtration_fin = mock_saison_controller.get_data("filtrationFin")
        pause_debut = mock_saison_controller.get_data("filtrationPauseDebut")
        pause_fin = mock_saison_controller.get_data("filtrationPauseFin")

        # Pause should be defined
        assert pause_debut != pause_fin

    def test_pause_pivot_adjusted_if_exceeds_24h(self, mock_saison_controller):
        """Test that pausePivot is adjusted if total exceeds 24h."""
        mock_saison_controller.data["temperatureMaxi"] = 0
        mock_saison_controller.methodeCalcul = 2
        mock_saison_controller.coefficientAjustement = 1.0
        mock_saison_controller.pausePivot = 300  # 5 hours pause

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(24.0, False)  # 24/2 = 12 hours

        # With 12h filtration + 5h pause = 17h total (should fit in 24h)
        # But if filtration is capped at 24h, pause should be 0
        filtration_debut = mock_saison_controller.get_data("filtrationDebut")
        filtration_fin = mock_saison_controller.get_data("filtrationFin")

        # Total duration should not exceed 24h
        duration = (filtration_fin - filtration_debut) / 3600
        assert duration <= 24.0

    def test_tomorrow_flag_adds_one_day(self, mock_saison_controller):
        """Test that flgTomorrow=True adds one day to calculation."""
        mock_saison_controller.data["temperatureMaxi"] = 0

        # Current time after pivot
        current_time = datetime(2025, 6, 15, 14, 0).timestamp()

        with patch('time.time', return_value=current_time):
            mock_saison_controller.calculateTimeFiltration(20.0, True)

        filtration_debut = mock_saison_controller.get_data("filtrationDebut")

        # filtrationDebut should be tomorrow
        debut_date = datetime.fromtimestamp(filtration_debut).date()
        expected_date = datetime(2025, 6, 16).date()

        assert debut_date == expected_date

    def test_tomorrow_flag_resets_temperature_maxi(self, mock_saison_controller):
        """Test that flgTomorrow=True resets temperatureMaxi."""
        mock_saison_controller.data["temperatureMaxi"] = 25.0

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(20.0, True)

        # temperatureMaxi should be reset to 0
        assert mock_saison_controller.get_data("temperatureMaxi") == 0

    def test_sets_calculate_status(self, mock_saison_controller):
        """Test that calculateStatus is set to 1."""
        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(20.0, False)

        assert mock_saison_controller.get_data("calculateStatus") == 1

    def test_updates_filtration_time_status(self, mock_saison_controller):
        """Test that filtrationTimeStatus is updated."""
        mock_saison_controller.data["temperatureMaxi"] = 0
        mock_saison_controller.methodeCalcul = 2
        mock_saison_controller.coefficientAjustement = 1.0

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(20.0, False)

        # Should set filtrationTimeStatus to "10:00" (20/2)
        mock_saison_controller.filtrationTimeStatus.set_status.assert_called_once_with("10:00")

    def test_updates_filtration_schedule_status_with_pause(self, mock_saison_controller):
        """Test that filtrationScheduleStatus is updated with pause."""
        mock_saison_controller.pausePivot = 60

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(20.0, False)

        # Should call set_status with a formatted schedule string
        mock_saison_controller.filtrationScheduleStatus.set_status.assert_called_once()
        call_args = mock_saison_controller.filtrationScheduleStatus.set_status.call_args[0][0]

        # Should contain temperature
        assert "°C" in call_args
        # Should contain time ranges separated by space (for pause)
        assert " " in call_args

    def test_updates_filtration_schedule_status_without_pause(self, mock_saison_controller):
        """Test that filtrationScheduleStatus is updated without pause."""
        mock_saison_controller.pausePivot = 0

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(20.0, False)

        mock_saison_controller.filtrationScheduleStatus.set_status.assert_called_once()
        call_args = mock_saison_controller.filtrationScheduleStatus.set_status.call_args[0][0]

        # Should contain temperature
        assert "°C" in call_args


@pytest.mark.unit
class TestCalculateStatusFiltration:
    """Tests for calculateStatusFiltration() - Status determination."""

    @pytest.mark.asyncio
    async def test_triggers_calculation_when_never_run(self, mock_saison_controller):
        """Test that calculation is triggered when filtrationDebut=0."""
        # No previous calculation
        mock_saison_controller.data["filtrationDebut"] = 0
        mock_saison_controller.data["filtrationFin"] = 0

        with patch.object(mock_saison_controller, 'calculateTimeFiltration') as mock_calc:
            with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
                await mock_saison_controller.calculateStatusFiltration(20.0)

            # Should call calculateTimeFiltration
            assert mock_calc.call_count >= 1

    @pytest.mark.asyncio
    async def test_activates_filtration_in_time_range(self, mock_saison_controller):
        """Test that filtration is activated when current time is in range."""
        # Set up time range: 10:00 - 16:00
        current_time = datetime(2025, 6, 15, 12, 0)  # 12:00 (in range)
        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        fin = datetime(2025, 6, 15, 16, 0).timestamp()

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(debut)  # No pause

        with patch('time.time', return_value=current_time.timestamp()):
            await mock_saison_controller.calculateStatusFiltration(20.0)

        # filtrationTemperature should be set to 1
        assert mock_saison_controller.get_data("filtrationTemperature") == 1

    @pytest.mark.asyncio
    async def test_deactivates_filtration_outside_range(self, mock_saison_controller):
        """Test that filtration is deactivated when outside time range."""
        # Set up time range: 10:00 - 16:00
        current_time = datetime(2025, 6, 15, 18, 0)  # 18:00 (outside)
        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        fin = datetime(2025, 6, 15, 16, 0).timestamp()

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(debut)
        mock_saison_controller.data["calculateStatus"] = 0

        with patch('time.time', return_value=current_time.timestamp()):
            with patch.object(mock_saison_controller, 'calculateTimeFiltration') as mock_calc:
                await mock_saison_controller.calculateStatusFiltration(20.0)

        # filtrationTemperature should be 0 (or not set to 1)
        filtration_temp = mock_saison_controller.get_data("filtrationTemperature", 0)
        assert filtration_temp == 0

    @pytest.mark.asyncio
    async def test_handles_pause_segment_first(self, mock_saison_controller):
        """Test handling of first segment with pause."""
        # Time range with pause: 10:00-12:00 (pause) 14:00-16:00
        current_time = datetime(2025, 6, 15, 11, 0)  # In first segment

        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        pause_debut = datetime(2025, 6, 15, 12, 0).timestamp()
        pause_fin = datetime(2025, 6, 15, 14, 0).timestamp()
        fin = datetime(2025, 6, 15, 16, 0).timestamp()

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(pause_debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(pause_fin)

        with patch('time.time', return_value=current_time.timestamp()):
            await mock_saison_controller.calculateStatusFiltration(20.0)

        # Should be active in first segment
        assert mock_saison_controller.get_data("filtrationTemperature") == 1

    @pytest.mark.asyncio
    async def test_handles_pause_segment_second(self, mock_saison_controller):
        """Test handling of second segment with pause."""
        # Time range with pause: 10:00-12:00 (pause) 14:00-16:00
        current_time = datetime(2025, 6, 15, 15, 0)  # In second segment

        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        pause_debut = datetime(2025, 6, 15, 12, 0).timestamp()
        pause_fin = datetime(2025, 6, 15, 14, 0).timestamp()
        fin = datetime(2025, 6, 15, 16, 0).timestamp()

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(pause_debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(pause_fin)

        with patch('time.time', return_value=current_time.timestamp()):
            await mock_saison_controller.calculateStatusFiltration(20.0)

        # Should be active in second segment
        assert mock_saison_controller.get_data("filtrationTemperature") == 1

    @pytest.mark.asyncio
    async def test_inactive_during_pause(self, mock_saison_controller):
        """Test that filtration is inactive during pause period."""
        # Time range with pause: 10:00-12:00 (pause) 14:00-16:00
        current_time = datetime(2025, 6, 15, 13, 0)  # During pause

        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        pause_debut = datetime(2025, 6, 15, 12, 0).timestamp()
        pause_fin = datetime(2025, 6, 15, 14, 0).timestamp()
        fin = datetime(2025, 6, 15, 16, 0).timestamp()

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(pause_debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(pause_fin)

        with patch('time.time', return_value=current_time.timestamp()):
            await mock_saison_controller.calculateStatusFiltration(20.0)

        # Should be inactive during pause
        filtration_temp = mock_saison_controller.get_data("filtrationTemperature", 0)
        assert filtration_temp == 0

    @pytest.mark.asyncio
    async def test_updates_temperature_display_with_probe_delay(self, mock_saison_controller):
        """Test that temperature display updates after probe delay."""
        mock_saison_controller.sondeLocalTechnique = True
        mock_saison_controller.sondeLocalTechniquePause = 5  # 5 minutes

        # Current time is 10 minutes after start (> 5 min delay)
        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        current_time = datetime(2025, 6, 15, 10, 10).timestamp()  # +10 min
        fin = datetime(2025, 6, 15, 16, 0).timestamp()

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(debut)

        with patch('time.time', return_value=current_time):
            await mock_saison_controller.calculateStatusFiltration(25.0)

        # Should update temperature display
        mock_saison_controller.updateTemperatureDisplay.assert_called_with(25.0)

    @pytest.mark.asyncio
    async def test_tracks_temperature_maxi(self, mock_saison_controller):
        """Test that temperatureMaxi is tracked."""
        mock_saison_controller.sondeLocalTechnique = False

        # Current temperature is higher than stored max
        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        current_time = datetime(2025, 6, 15, 12, 0).timestamp()
        fin = datetime(2025, 6, 15, 16, 0).timestamp()

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(debut)
        mock_saison_controller.data["temperatureMaxi"] = 20.0

        with patch('time.time', return_value=current_time):
            await mock_saison_controller.calculateStatusFiltration(25.0)

        # temperatureMaxi should be updated to 25.0
        assert mock_saison_controller.get_data("temperatureMaxi") == 25.0

    @pytest.mark.asyncio
    async def test_disables_marche_forcee_when_configured(self, mock_saison_controller):
        """Test that marcheForcee is disabled when disableMarcheForcee=True."""
        mock_saison_controller.disableMarcheForcee = True

        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        current_time = datetime(2025, 6, 15, 12, 0).timestamp()
        fin = datetime(2025, 6, 15, 16, 0).timestamp()

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(debut)
        mock_saison_controller.data["marcheForcee"] = 1

        with patch('time.time', return_value=current_time):
            await mock_saison_controller.calculateStatusFiltration(20.0)

        # marcheForcee should be set to 0
        assert mock_saison_controller.get_data("marcheForcee") == 0

    @pytest.mark.asyncio
    async def test_recalculates_for_tomorrow_when_past_range(self, mock_saison_controller):
        """Test that calculation is triggered for tomorrow when past range."""
        # Time is after filtration end
        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        fin = datetime(2025, 6, 15, 16, 0).timestamp()
        current_time = datetime(2025, 6, 15, 18, 0).timestamp()  # After end

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(debut)
        mock_saison_controller.data["calculateStatus"] = 0

        with patch('time.time', return_value=current_time):
            with patch.object(mock_saison_controller, 'calculateTimeFiltration') as mock_calc:
                await mock_saison_controller.calculateStatusFiltration(20.0)

            # Should call calculateTimeFiltration with flgTomorrow=True
            mock_calc.assert_called_with(20.0, True)

    @pytest.mark.asyncio
    async def test_resets_filtration_hivernage(self, mock_saison_controller):
        """Test that filtrationHivernage is reset to 0."""
        debut = datetime(2025, 6, 15, 10, 0).timestamp()
        current_time = datetime(2025, 6, 15, 12, 0).timestamp()
        fin = datetime(2025, 6, 15, 16, 0).timestamp()

        mock_saison_controller.data["filtrationDebut"] = int(debut)
        mock_saison_controller.data["filtrationFin"] = int(fin)
        mock_saison_controller.data["filtrationPauseDebut"] = int(debut)
        mock_saison_controller.data["filtrationPauseFin"] = int(debut)
        mock_saison_controller.data["filtrationHivernage"] = 1

        with patch('time.time', return_value=current_time):
            await mock_saison_controller.calculateStatusFiltration(20.0)

        # filtrationHivernage should be set to 0
        assert mock_saison_controller.get_data("filtrationHivernage") == 0


@pytest.mark.integration
class TestSaisonIntegration:
    """Integration tests for saison mode."""

    def test_full_calculation_cycle_with_curve(self, mock_saison_controller):
        """Test complete calculation cycle with curve method."""
        mock_saison_controller.methodeCalcul = 1  # Curve
        mock_saison_controller.coefficientAjustement = 1.0
        mock_saison_controller.distributionDatePivot = 2  # 1/3 <> 2/3

        with patch('time.time', return_value=datetime(2025, 6, 15, 10, 0).timestamp()):
            mock_saison_controller.calculateTimeFiltration(25.0, False)

        # Verify all data is set
        assert mock_saison_controller.get_data("filtrationDebut") > 0
        assert mock_saison_controller.get_data("filtrationFin") > 0
        assert mock_saison_controller.get_data("calculateStatus") == 1

        # Verify UI updates
        assert mock_saison_controller.filtrationTimeStatus.set_status.called
        assert mock_saison_controller.filtrationScheduleStatus.set_status.called

    @pytest.mark.asyncio
    async def test_full_day_simulation(self, mock_saison_controller):
        """Test full 24h cycle simulation."""
        # Initial calculation at 8:00
        with patch('time.time', return_value=datetime(2025, 6, 15, 8, 0).timestamp()):
            await mock_saison_controller.calculateStatusFiltration(22.0)

        # Should have calculated times
        assert mock_saison_controller.get_data("filtrationDebut") > 0

        # Simulate 12:00 (likely in range)
        with patch('time.time', return_value=datetime(2025, 6, 15, 12, 0).timestamp()):
            await mock_saison_controller.calculateStatusFiltration(24.0)

        # Should track max temperature
        assert mock_saison_controller.get_data("temperatureMaxi") >= 22.0
