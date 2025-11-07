"""Utility functions for safe service calls in Pool Control integration."""

import asyncio
import logging
from typing import Optional

from homeassistant.core import HomeAssistant

from .errors import (
    EntityNotConfiguredError,
    EntityNotFoundError,
    InvalidEntityIdError,
    ServiceCallError,
    StateVerificationError,
)

_LOGGER = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
STATE_VERIFICATION_DELAY = 0.5


class ServiceUtilsMixin:
    """Mixin providing safe service call utilities for pool control."""

    def _parse_entity_domain(self, entity_id: str) -> str:
        """Parse and validate an entity_id, returning the domain.

        Args:
            entity_id: The entity ID to parse (e.g., "switch.filtration")

        Returns:
            The domain part (e.g., "switch")

        Raises:
            InvalidEntityIdError: If the entity_id format is invalid
        """

        if not entity_id or not isinstance(entity_id, str):
            raise InvalidEntityIdError(entity_id)

        if "." not in entity_id:
            raise InvalidEntityIdError(entity_id)

        parts = entity_id.split(".", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise InvalidEntityIdError(entity_id)

        return parts[0]

    def _validate_entity_exists(self, entity_id: str) -> None:
        """Validate that an entity exists in Home Assistant.

        Args:
            entity_id: The entity ID to validate

        Raises:
            EntityNotFoundError: If the entity does not exist
        """

        state = self.hass.states.get(entity_id)
        if state is None:
            raise EntityNotFoundError(entity_id)

    async def _safe_call_service(
        self,
        entity_id: str,
        service: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        verify_state: Optional[str] = None,
    ) -> bool:
        """Call a Home Assistant service with error handling and retry logic.

        Args:
            entity_id: The entity ID to control
            service: The service to call ("turn_on", "turn_off", etc.)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay in seconds between retries
            verify_state: If provided, verify the entity reached this state

        Returns:
            True if the service call succeeded, False otherwise

        Raises:
            EntityNotConfiguredError: If entity_id is None or empty
            InvalidEntityIdError: If entity_id format is invalid
            EntityNotFoundError: If the entity does not exist
            ServiceCallError: If all retry attempts fail
        """

        # Validate entity_id is configured
        if not entity_id:
            raise EntityNotConfiguredError("entity_id")

        # Parse and validate entity_id format
        try:
            domain = self._parse_entity_domain(entity_id)
        except InvalidEntityIdError:
            _LOGGER.error("Invalid entity_id format: %s", entity_id)
            raise

        # Validate entity exists
        try:
            self._validate_entity_exists(entity_id)
        except EntityNotFoundError:
            _LOGGER.error("Entity %s not found", entity_id)
            raise

        # Attempt service call with retries
        last_exception = None
        for attempt in range(max_retries):
            try:
                _LOGGER.debug(
                    "Calling service %s.%s on %s (attempt %d/%d)",
                    domain,
                    service,
                    entity_id,
                    attempt + 1,
                    max_retries,
                )

                await self.hass.services.async_call(
                    domain,
                    service,
                    {"entity_id": entity_id},
                )

                # Verify state if requested
                if verify_state:
                    await asyncio.sleep(STATE_VERIFICATION_DELAY)
                    if not await self._verify_state(entity_id, verify_state):
                        raise StateVerificationError(
                            entity_id,
                            verify_state,
                            self.hass.states.get(entity_id).state
                            if self.hass.states.get(entity_id)
                            else "unknown",
                        )

                _LOGGER.debug(
                    "Successfully called service %s.%s on %s", domain, service, entity_id
                )
                return True

            except Exception as e:
                last_exception = e
                _LOGGER.warning(
                    "Service call %s.%s on %s failed (attempt %d/%d): %s",
                    domain,
                    service,
                    entity_id,
                    attempt + 1,
                    max_retries,
                    e,
                )

                # Don't retry on validation errors
                if isinstance(
                    e,
                    (
                        EntityNotConfiguredError,
                        InvalidEntityIdError,
                        EntityNotFoundError,
                    ),
                ):
                    raise

                # Wait before retry (except on last attempt)
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)

        # All retries failed
        error_msg = f"Failed to call service {domain}.{service} on {entity_id} after {max_retries} attempts"
        _LOGGER.error("%s: %s", error_msg, last_exception)
        raise ServiceCallError(entity_id, service, error_msg)

    async def _verify_state(
        self, entity_id: str, expected_state: str, timeout: float = 2.0
    ) -> bool:
        """Verify that an entity has reached the expected state.

        Args:
            entity_id: The entity ID to check
            expected_state: The expected state ("on", "off", etc.)
            timeout: Maximum time to wait for state change

        Returns:
            True if the entity reached the expected state, False otherwise
        """

        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            state = self.hass.states.get(entity_id)
            if state and state.state == expected_state:
                _LOGGER.debug(
                    "Entity %s reached expected state: %s", entity_id, expected_state
                )
                return True

            await asyncio.sleep(0.1)

        actual_state = self.hass.states.get(entity_id)
        _LOGGER.warning(
            "Entity %s did not reach expected state %s within %s seconds (current state: %s)",
            entity_id,
            expected_state,
            timeout,
            actual_state.state if actual_state else "unknown",
        )
        return False

    async def _notify_error(self, title: str, message: str) -> None:
        """Send a persistent notification to Home Assistant.

        Args:
            title: The notification title
            message: The notification message
        """

        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                service_data={
                    "title": title,
                    "message": message,
                    "notification_id": f"pool_control_error_{asyncio.get_event_loop().time()}",
                },
            )
            _LOGGER.info("Sent error notification: %s - %s", title, message)
        except Exception as e:
            _LOGGER.error("Failed to send notification: %s", e)
