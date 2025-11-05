"""Custom exceptions for Pool Control integration."""


class PoolControlError(Exception):
    """Base exception for Pool Control."""

    pass


class EntityNotFoundError(PoolControlError):
    """Exception raised when an entity is not found."""

    def __init__(self, entity_id: str, message: str = "") -> None:
        """Initialize EntityNotFoundError."""

        self.entity_id = entity_id
        if not message:
            message = f"Entity '{entity_id}' not found"
        super().__init__(message)


class EntityNotConfiguredError(PoolControlError):
    """Exception raised when an entity is not configured."""

    def __init__(self, entity_name: str, message: str = "") -> None:
        """Initialize EntityNotConfiguredError."""

        self.entity_name = entity_name
        if not message:
            message = f"Entity '{entity_name}' is not configured"
        super().__init__(message)


class ServiceCallError(PoolControlError):
    """Exception raised when a service call fails."""

    def __init__(self, entity_id: str, service: str, message: str = "") -> None:
        """Initialize ServiceCallError."""

        self.entity_id = entity_id
        self.service = service
        if not message:
            message = f"Failed to call service '{service}' on '{entity_id}'"
        super().__init__(message)


class InvalidEntityIdError(PoolControlError):
    """Exception raised when an entity ID has invalid format."""

    def __init__(self, entity_id: str, message: str = "") -> None:
        """Initialize InvalidEntityIdError."""

        self.entity_id = entity_id
        if not message:
            message = f"Invalid entity_id format: '{entity_id}'"
        super().__init__(message)


class StateVerificationError(PoolControlError):
    """Exception raised when state verification fails."""

    def __init__(
        self, entity_id: str, expected_state: str, actual_state: str, message: str = ""
    ) -> None:
        """Initialize StateVerificationError."""

        self.entity_id = entity_id
        self.expected_state = expected_state
        self.actual_state = actual_state
        if not message:
            message = f"State verification failed for '{entity_id}': expected '{expected_state}', got '{actual_state}'"
        super().__init__(message)
