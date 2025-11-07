"""Tests for error handling in Pool Control integration."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from custom_components.pool_control.errors import (
    EntityNotConfiguredError,
    EntityNotFoundError,
    InvalidEntityIdError,
    PoolControlError,
    ServiceCallError,
    StateVerificationError,
)
from custom_components.pool_control.service_utils import ServiceUtilsMixin


class TestCustomExceptions:
    """Test custom exceptions."""

    def test_pool_control_error(self) -> None:
        """Test PoolControlError base exception."""
        error = PoolControlError("Test error")
        assert str(error) == "Test error"

    def test_entity_not_found_error(self) -> None:
        """Test EntityNotFoundError exception."""
        error = EntityNotFoundError("switch.filtration")
        assert error.entity_id == "switch.filtration"
        assert "switch.filtration" in str(error)
        assert "not found" in str(error)

    def test_entity_not_configured_error(self) -> None:
        """Test EntityNotConfiguredError exception."""
        error = EntityNotConfiguredError("filtration")
        assert error.entity_name == "filtration"
        assert "filtration" in str(error)
        assert "not configured" in str(error)

    def test_service_call_error(self) -> None:
        """Test ServiceCallError exception."""
        error = ServiceCallError("switch.filtration", "turn_on")
        assert error.entity_id == "switch.filtration"
        assert error.service == "turn_on"
        assert "switch.filtration" in str(error)
        assert "turn_on" in str(error)

    def test_invalid_entity_id_error(self) -> None:
        """Test InvalidEntityIdError exception."""
        error = InvalidEntityIdError("invalid_id")
        assert error.entity_id == "invalid_id"
        assert "invalid_id" in str(error)

    def test_state_verification_error(self) -> None:
        """Test StateVerificationError exception."""
        error = StateVerificationError("switch.filtration", "on", "off")
        assert error.entity_id == "switch.filtration"
        assert error.expected_state == "on"
        assert error.actual_state == "off"
        assert "switch.filtration" in str(error)
        assert "expected 'on'" in str(error)
        assert "got 'off'" in str(error)


class TestServiceUtilsMixin:
    """Test ServiceUtilsMixin functionality."""

    @pytest.fixture
    def mock_hass(self) -> Mock:
        """Create a mock HomeAssistant instance."""
        hass = Mock()
        hass.states.get = Mock()
        hass.services.async_call = AsyncMock()
        return hass

    @pytest.fixture
    def service_utils(self, mock_hass: Mock) -> ServiceUtilsMixin:
        """Create a ServiceUtilsMixin instance."""
        mixin = ServiceUtilsMixin()
        mixin.hass = mock_hass
        return mixin

    def test_parse_entity_domain_valid(self, service_utils: ServiceUtilsMixin) -> None:
        """Test parsing a valid entity_id."""
        domain = service_utils._parse_entity_domain("switch.filtration")
        assert domain == "switch"

    def test_parse_entity_domain_invalid_no_dot(
        self, service_utils: ServiceUtilsMixin
    ) -> None:
        """Test parsing an entity_id without a dot."""
        with pytest.raises(InvalidEntityIdError) as exc_info:
            service_utils._parse_entity_domain("invalid_id")
        assert "invalid_id" in str(exc_info.value)

    def test_parse_entity_domain_invalid_empty(
        self, service_utils: ServiceUtilsMixin
    ) -> None:
        """Test parsing an empty entity_id."""
        with pytest.raises(InvalidEntityIdError):
            service_utils._parse_entity_domain("")

    def test_parse_entity_domain_invalid_none(
        self, service_utils: ServiceUtilsMixin
    ) -> None:
        """Test parsing a None entity_id."""
        with pytest.raises(InvalidEntityIdError):
            service_utils._parse_entity_domain(None)  # type: ignore

    def test_validate_entity_exists_success(
        self, service_utils: ServiceUtilsMixin, mock_hass: Mock
    ) -> None:
        """Test validating an existing entity."""
        mock_state = Mock()
        mock_state.state = "on"
        mock_hass.states.get.return_value = mock_state

        # Should not raise
        service_utils._validate_entity_exists("switch.filtration")

    def test_validate_entity_exists_not_found(
        self, service_utils: ServiceUtilsMixin, mock_hass: Mock
    ) -> None:
        """Test validating a non-existent entity."""
        mock_hass.states.get.return_value = None

        with pytest.raises(EntityNotFoundError) as exc_info:
            service_utils._validate_entity_exists("switch.filtration")
        assert exc_info.value.entity_id == "switch.filtration"

    @pytest.mark.asyncio
    async def test_safe_call_service_success(
        self, service_utils: ServiceUtilsMixin, mock_hass: Mock
    ) -> None:
        """Test successful service call."""
        mock_state = Mock()
        mock_state.state = "on"
        mock_hass.states.get.return_value = mock_state

        result = await service_utils._safe_call_service(
            "switch.filtration", "turn_on"
        )

        assert result is True
        mock_hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_safe_call_service_entity_not_configured(
        self, service_utils: ServiceUtilsMixin
    ) -> None:
        """Test service call with unconfigured entity."""
        with pytest.raises(EntityNotConfiguredError):
            await service_utils._safe_call_service(None, "turn_on")  # type: ignore

    @pytest.mark.asyncio
    async def test_safe_call_service_entity_not_found(
        self, service_utils: ServiceUtilsMixin, mock_hass: Mock
    ) -> None:
        """Test service call with non-existent entity."""
        mock_hass.states.get.return_value = None

        with pytest.raises(EntityNotFoundError):
            await service_utils._safe_call_service("switch.filtration", "turn_on")

    @pytest.mark.asyncio
    async def test_safe_call_service_retry_on_failure(
        self, service_utils: ServiceUtilsMixin, mock_hass: Mock
    ) -> None:
        """Test service call retry logic on transient failures."""
        mock_state = Mock()
        mock_state.state = "on"
        mock_hass.states.get.return_value = mock_state

        # First two calls fail, third succeeds
        mock_hass.services.async_call.side_effect = [
            Exception("Transient error"),
            Exception("Transient error"),
            None,
        ]

        result = await service_utils._safe_call_service(
            "switch.filtration", "turn_on", max_retries=3, retry_delay=0.01
        )

        assert result is True
        assert mock_hass.services.async_call.call_count == 3

    @pytest.mark.asyncio
    async def test_safe_call_service_max_retries_exceeded(
        self, service_utils: ServiceUtilsMixin, mock_hass: Mock
    ) -> None:
        """Test service call when max retries are exceeded."""
        mock_state = Mock()
        mock_state.state = "on"
        mock_hass.states.get.return_value = mock_state

        # All calls fail
        mock_hass.services.async_call.side_effect = Exception("Persistent error")

        with pytest.raises(ServiceCallError):
            await service_utils._safe_call_service(
                "switch.filtration", "turn_on", max_retries=3, retry_delay=0.01
            )

        assert mock_hass.services.async_call.call_count == 3

    @pytest.mark.asyncio
    async def test_verify_state_success(
        self, service_utils: ServiceUtilsMixin, mock_hass: Mock
    ) -> None:
        """Test successful state verification."""
        mock_state = Mock()
        mock_state.state = "on"
        mock_hass.states.get.return_value = mock_state

        result = await service_utils._verify_state("switch.filtration", "on", timeout=0.1)

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_state_timeout(
        self, service_utils: ServiceUtilsMixin, mock_hass: Mock
    ) -> None:
        """Test state verification timeout."""
        mock_state = Mock()
        mock_state.state = "off"
        mock_hass.states.get.return_value = mock_state

        result = await service_utils._verify_state("switch.filtration", "on", timeout=0.1)

        assert result is False

    @pytest.mark.asyncio
    async def test_notify_error(
        self, service_utils: ServiceUtilsMixin, mock_hass: Mock
    ) -> None:
        """Test error notification."""
        await service_utils._notify_error("Test Title", "Test message")

        mock_hass.services.async_call.assert_called_once()
        call_args = mock_hass.services.async_call.call_args
        assert call_args[0][0] == "persistent_notification"
        assert call_args[0][1] == "create"
        assert call_args[1]["title"] == "Test Title"
        assert call_args[1]["message"] == "Test message"
