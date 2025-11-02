"""Tests for utils.py module - Filtration time calculation utilities.

Tests the utility methods that calculate pool filtration times based on water temperature.
The module provides different calculation methods:
- processingTime: Convert hours to seconds and formatted string
- calculateTimeFiltrationWithCurve: Cubic equation method (complex)
- calculateTimeFiltrationWithTemperatureReducedByHalf: Simple temp/2 method
- calculateTimeFiltrationWithTemperatureHivernage: Winter mode temp/3 method

Functions tested:
1. processingTime(dureeHeures) - Time conversion and formatting
2. calculateTimeFiltrationWithCurve(temperatureWater) - Cubic equation calculation
3. calculateTimeFiltrationWithTemperatureReducedByHalf(temperatureWater) - Simple method
4. calculateTimeFiltrationWithTemperatureHivernage(temperatureWater) - Winter method
"""

import pytest
from unittest.mock import Mock

# Skip all tests if Home Assistant is not installed
pytest.importorskip("homeassistant")


@pytest.fixture
def mock_utils_controller(mock_hass, mock_pool_config):
    """Create a mock controller with FiltrationUtilsMixin."""
    from custom_components.pool_control.controller import PoolController

    controller = PoolController(mock_hass, mock_pool_config)

    # Set default coefficients
    controller.coefficientAjustement = 1.0
    controller.coefficientAjustementHivernage = 1.0
    controller.tempsDeFiltrationMinimum = 3.0  # 3 hours minimum

    return controller


@pytest.mark.unit
class TestProcessingTime:
    """Tests for processingTime() - Time conversion and formatting."""

    def test_converts_hours_to_seconds(self, mock_utils_controller):
        """Test processingTime converts hours to seconds correctly."""
        seconds, formatted = mock_utils_controller.processingTime(2.0)

        # 2 hours = 7200 seconds
        assert seconds == 7200.0

    def test_formats_hours_and_minutes(self, mock_utils_controller):
        """Test processingTime formats time as HH:MM."""
        seconds, formatted = mock_utils_controller.processingTime(2.5)

        # 2.5 hours = 2h30m
        assert formatted == "02:30"

    def test_rounds_to_minute_precision(self, mock_utils_controller):
        """Test processingTime rounds to minute precision."""
        # 2.517 hours = 2h31m (2 * 60 + 31 = 151 minutes, rounded from 151.02)
        seconds, formatted = mock_utils_controller.processingTime(2.517)

        # Should round to nearest minute
        assert formatted == "02:31"

    def test_caps_at_24_hours(self, mock_utils_controller):
        """Test processingTime caps duration at 24 hours."""
        seconds, formatted = mock_utils_controller.processingTime(30.0)

        # Should be capped at 24 hours
        assert seconds == 24.0 * 3600.0
        assert formatted == "24:00"

    def test_handles_zero_hours(self, mock_utils_controller):
        """Test processingTime handles zero hours."""
        seconds, formatted = mock_utils_controller.processingTime(0.0)

        assert seconds == 0.0
        assert formatted == "00:00"

    def test_handles_fractional_minutes(self, mock_utils_controller):
        """Test processingTime handles fractional minutes correctly."""
        # 1.25 hours = 1h15m
        seconds, formatted = mock_utils_controller.processingTime(1.25)

        assert seconds == 4500.0  # 1.25 * 3600
        assert formatted == "01:15"

    def test_handles_small_values(self, mock_utils_controller):
        """Test processingTime handles small time values."""
        # 0.5 hours = 30 minutes
        seconds, formatted = mock_utils_controller.processingTime(0.5)

        assert seconds == 1800.0
        assert formatted == "00:30"

    def test_formatting_pads_single_digits(self, mock_utils_controller):
        """Test processingTime pads single digits with zeros."""
        # 3 hours 5 minutes
        seconds, formatted = mock_utils_controller.processingTime(3.0833)

        assert formatted == "03:05"

    def test_handles_exact_hours(self, mock_utils_controller):
        """Test processingTime handles exact hour values."""
        seconds, formatted = mock_utils_controller.processingTime(8.0)

        assert seconds == 28800.0
        assert formatted == "08:00"

    def test_rounding_behavior(self, mock_utils_controller):
        """Test processingTime rounding behavior for edge cases."""
        # Test that rounding happens correctly
        # 2.0083 hours = 120.5 minutes, should round to 120 minutes
        seconds, formatted = mock_utils_controller.processingTime(2.0083)

        # After rounding to minutes: 120 minutes = 2 hours
        assert formatted == "02:00"


@pytest.mark.unit
class TestCalculateTimeFiltrationWithCurve:
    """Tests for calculateTimeFiltrationWithCurve() - Cubic equation calculation."""

    def test_applies_minimum_temperature(self, mock_utils_controller):
        """Test calculation enforces minimum temperature of 10°C."""
        # Temperature below 10°C should be treated as 10°C
        result_5 = mock_utils_controller.calculateTimeFiltrationWithCurve(5.0)
        result_10 = mock_utils_controller.calculateTimeFiltrationWithCurve(10.0)

        # Both should give same result
        assert result_5 == result_10

    def test_calculation_at_10_degrees(self, mock_utils_controller):
        """Test calculation at minimum temperature (10°C)."""
        result = mock_utils_controller.calculateTimeFiltrationWithCurve(10.0)

        # Manually calculate: a*10³ + b*10² + c*10 + d
        # a=0.00335, b=-0.14953, c=2.43489, d=-10.72859
        expected = (0.00335 * 1000) + (-0.14953 * 100) + (2.43489 * 10) + (-10.72859)
        expected = 3.35 - 14.953 + 24.3489 - 10.72859
        # = 2.01731

        assert abs(result - expected) < 0.001

    def test_calculation_at_20_degrees(self, mock_utils_controller):
        """Test calculation at moderate temperature (20°C)."""
        result = mock_utils_controller.calculateTimeFiltrationWithCurve(20.0)

        # Manually calculate: a*20³ + b*20² + c*20 + d
        expected = (0.00335 * 8000) + (-0.14953 * 400) + (2.43489 * 20) + (-10.72859)
        expected = 26.8 - 59.812 + 48.6978 - 10.72859
        # = 4.95741

        assert abs(result - expected) < 0.001

    def test_calculation_at_30_degrees(self, mock_utils_controller):
        """Test calculation at high temperature (30°C)."""
        result = mock_utils_controller.calculateTimeFiltrationWithCurve(30.0)

        # At 30°C, result should be higher due to cubic growth
        # Manually calculate: a*30³ + b*30² + c*30 + d
        expected = (0.00335 * 27000) + (-0.14953 * 900) + (2.43489 * 30) + (-10.72859)
        expected = 90.45 - 134.577 + 73.0467 - 10.72859
        # = 18.19111

        assert abs(result - expected) < 0.001

    def test_applies_adjustment_coefficient(self, mock_utils_controller):
        """Test calculation applies adjustment coefficient correctly."""
        mock_utils_controller.coefficientAjustement = 1.5

        result = mock_utils_controller.calculateTimeFiltrationWithCurve(20.0)

        # With coeff=1.5, all coefficients are multiplied
        a = 0.00335 * 1.5
        b = -0.14953 * 1.5
        c = 2.43489 * 1.5
        d = -10.72859 * 1.5

        expected = (a * 8000) + (b * 400) + (c * 20) + d

        assert abs(result - expected) < 0.001

    def test_coefficient_zero(self, mock_utils_controller):
        """Test calculation with zero coefficient."""
        mock_utils_controller.coefficientAjustement = 0.0

        result = mock_utils_controller.calculateTimeFiltrationWithCurve(20.0)

        # With coeff=0, result should be 0
        assert result == 0.0

    def test_negative_temperature_uses_minimum(self, mock_utils_controller):
        """Test negative temperatures use minimum of 10°C."""
        result_neg = mock_utils_controller.calculateTimeFiltrationWithCurve(-5.0)
        result_10 = mock_utils_controller.calculateTimeFiltrationWithCurve(10.0)

        assert result_neg == result_10

    def test_increases_with_temperature(self, mock_utils_controller):
        """Test filtration time increases with temperature."""
        result_15 = mock_utils_controller.calculateTimeFiltrationWithCurve(15.0)
        result_20 = mock_utils_controller.calculateTimeFiltrationWithCurve(20.0)
        result_25 = mock_utils_controller.calculateTimeFiltrationWithCurve(25.0)

        # Should be monotonically increasing
        assert result_15 < result_20 < result_25


@pytest.mark.unit
class TestCalculateTimeFiltrationWithTemperatureReducedByHalf:
    """Tests for calculateTimeFiltrationWithTemperatureReducedByHalf() - Simple temp/2."""

    def test_divides_temperature_by_two(self, mock_utils_controller):
        """Test calculation divides temperature by 2."""
        result = mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
            20.0
        )

        # 20 / 2 = 10 hours
        assert result == 10.0

    def test_applies_adjustment_coefficient(self, mock_utils_controller):
        """Test calculation applies adjustment coefficient."""
        mock_utils_controller.coefficientAjustement = 1.5

        result = mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
            20.0
        )

        # (20 / 2) * 1.5 = 15 hours
        assert result == 15.0

    def test_handles_zero_temperature(self, mock_utils_controller):
        """Test calculation handles zero temperature."""
        result = mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
            0.0
        )

        assert result == 0.0

    def test_handles_fractional_temperature(self, mock_utils_controller):
        """Test calculation handles fractional temperatures."""
        result = mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
            25.5
        )

        # 25.5 / 2 = 12.75 hours
        assert result == 12.75

    def test_coefficient_zero(self, mock_utils_controller):
        """Test calculation with zero coefficient."""
        mock_utils_controller.coefficientAjustement = 0.0

        result = mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
            20.0
        )

        assert result == 0.0

    def test_increases_linearly_with_temperature(self, mock_utils_controller):
        """Test filtration time increases linearly with temperature."""
        result_10 = mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
            10.0
        )
        result_20 = mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
            20.0
        )
        result_30 = mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
            30.0
        )

        # Should be linear: double temp = double result
        assert result_20 == result_10 * 2
        assert result_30 == result_10 * 3


@pytest.mark.unit
class TestCalculateTimeFiltrationWithTemperatureHivernage:
    """Tests for calculateTimeFiltrationWithTemperatureHivernage() - Winter temp/3."""

    def test_divides_temperature_by_three(self, mock_utils_controller):
        """Test calculation divides temperature by 3."""
        result = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(15.0)
        )

        # 15 / 3 = 5 hours
        assert result == 5.0

    def test_applies_hivernage_coefficient(self, mock_utils_controller):
        """Test calculation applies hivernage adjustment coefficient."""
        mock_utils_controller.coefficientAjustementHivernage = 2.0

        result = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(15.0)
        )

        # (15 / 3) * 2.0 = 10 hours
        assert result == 10.0

    def test_enforces_minimum_time(self, mock_utils_controller):
        """Test calculation enforces minimum filtration time."""
        mock_utils_controller.tempsDeFiltrationMinimum = 3.0

        result = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(6.0)
        )

        # 6 / 3 = 2 hours, but minimum is 3 hours
        assert result == 3.0

    def test_minimum_does_not_apply_when_above(self, mock_utils_controller):
        """Test minimum time doesn't apply when calculated time is higher."""
        mock_utils_controller.tempsDeFiltrationMinimum = 3.0

        result = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(15.0)
        )

        # 15 / 3 = 5 hours, which is > 3 hours minimum
        assert result == 5.0

    def test_handles_very_low_temperature(self, mock_utils_controller):
        """Test calculation handles very low temperatures."""
        mock_utils_controller.tempsDeFiltrationMinimum = 3.0

        result = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(3.0)
        )

        # 3 / 3 = 1 hour, but minimum is 3 hours
        assert result == 3.0

    def test_coefficient_affects_minimum_check(self, mock_utils_controller):
        """Test coefficient is applied before minimum check."""
        mock_utils_controller.coefficientAjustementHivernage = 2.0
        mock_utils_controller.tempsDeFiltrationMinimum = 3.0

        result = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(6.0)
        )

        # (6 / 3) * 2.0 = 4 hours, which is > 3 hours minimum
        assert result == 4.0

    def test_increases_linearly_with_temperature(self, mock_utils_controller):
        """Test filtration time increases linearly with temperature (above minimum)."""
        mock_utils_controller.tempsDeFiltrationMinimum = 0.0  # Disable minimum

        result_15 = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(15.0)
        )
        result_30 = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(30.0)
        )

        # Should be linear: double temp = double result
        assert result_30 == result_15 * 2


@pytest.mark.integration
class TestUtilsIntegration:
    """Integration tests for utility functions."""

    def test_complete_filtration_calculation_pipeline(self, mock_utils_controller):
        """Test complete pipeline: calculate hours then process to time format."""
        # Calculate hours using curve method
        hours = mock_utils_controller.calculateTimeFiltrationWithCurve(25.0)

        # Process to get seconds and formatted time
        seconds, formatted = mock_utils_controller.processingTime(hours)

        # Verify both outputs are valid
        assert seconds > 0
        assert ":" in formatted
        assert len(formatted) == 5  # HH:MM format

    def test_three_methods_produce_different_results(self, mock_utils_controller):
        """Test that the three calculation methods produce different results."""
        temp = 24.0

        result_curve = mock_utils_controller.calculateTimeFiltrationWithCurve(temp)
        result_half = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
                temp
            )
        )
        result_hivernage = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(temp)
        )

        # All three methods should give different results for the same temperature
        assert result_curve != result_half
        assert result_half != result_hivernage
        assert result_curve != result_hivernage

    def test_coefficient_affects_all_methods(self, mock_utils_controller):
        """Test adjustment coefficients affect all calculation methods."""
        # Test with default coefficient
        result_curve_1 = mock_utils_controller.calculateTimeFiltrationWithCurve(20.0)
        result_half_1 = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
                20.0
            )
        )

        # Change coefficient
        mock_utils_controller.coefficientAjustement = 1.5

        result_curve_2 = mock_utils_controller.calculateTimeFiltrationWithCurve(20.0)
        result_half_2 = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
                20.0
            )
        )

        # Results should be different with different coefficients
        assert result_curve_2 == result_curve_1 * 1.5
        assert result_half_2 == result_half_1 * 1.5

    def test_processing_time_handles_all_method_outputs(self, mock_utils_controller):
        """Test processingTime can handle outputs from all calculation methods."""
        temp = 22.0

        hours_curve = mock_utils_controller.calculateTimeFiltrationWithCurve(temp)
        hours_half = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureReducedByHalf(
                temp
            )
        )
        hours_hivernage = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(temp)
        )

        # All should process without errors
        seconds1, formatted1 = mock_utils_controller.processingTime(hours_curve)
        seconds2, formatted2 = mock_utils_controller.processingTime(hours_half)
        seconds3, formatted3 = mock_utils_controller.processingTime(hours_hivernage)

        # All should produce valid formatted times
        assert all(":" in fmt for fmt in [formatted1, formatted2, formatted3])
        assert all(len(fmt) == 5 for fmt in [formatted1, formatted2, formatted3])

    def test_extreme_coefficient_values(self, mock_utils_controller):
        """Test extreme coefficient values don't cause errors."""
        mock_utils_controller.coefficientAjustement = 10.0

        # Should not crash with extreme values
        result = mock_utils_controller.calculateTimeFiltrationWithCurve(25.0)
        seconds, formatted = mock_utils_controller.processingTime(result)

        # Result should be capped at 24 hours
        assert seconds <= 24.0 * 3600.0
        assert formatted == "24:00"

    def test_hivernage_minimum_with_zero_coefficient(self, mock_utils_controller):
        """Test hivernage method respects minimum even with zero coefficient."""
        mock_utils_controller.coefficientAjustementHivernage = 0.0
        mock_utils_controller.tempsDeFiltrationMinimum = 3.0

        result = (
            mock_utils_controller.calculateTimeFiltrationWithTemperatureHivernage(20.0)
        )

        # Even with 0 coefficient, should return minimum
        assert result == 3.0
