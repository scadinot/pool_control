"""Entities for Pool Control integration."""

import logging
from typing import Any, Callable, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorEntity

_LOGGER = logging.getLogger(__name__)


class PoolControlStatusSensor(SensorEntity):
    """Sensor générique pour afficher un statut Pool Control."""

    def __init__(
        self,
        controller: Any,
        name: str,
        unique_id: str,
        controller_attribute_name: str,
        default_state: str = "Arrêté",
    ) -> None:
        """Initialize the PoolControlStatusSensor."""

        self._controller = controller
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._controller_attribute_name = controller_attribute_name
        self._state = default_state
        self._ready = False

        # Dès la création, on attache l'entité au controller dynamiquement
        setattr(controller, controller_attribute_name, self)

    async def async_added_to_hass(self) -> None:
        """Call when the entity is added to hass."""

        self._ready = True

    @property
    def state(self) -> str:
        """Return the state of the sensor."""

        return self._state

    def set_status(self, value: str) -> None:
        """Set the status of the sensor."""

        self._state = value
        if self._ready:
            self.async_write_ha_state()


class PoolControlButton(ButtonEntity):
    """Button générique pour Pool Control."""

    def __init__(self, controller: Any, name: str, unique_id: str, callback: Callable) -> None:
        """Initialize the PoolControlButton."""

        self._controller = controller
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._callback = callback

    async def async_press(self) -> None:
        """Handle the button press."""

        if self._callback:
            try:
                _LOGGER.info("Button '%s' pressed", self._attr_name)
                await self._callback()
                _LOGGER.debug("Button '%s' executed successfully", self._attr_name)
            except Exception as e:
                _LOGGER.exception(
                    "Error executing button '%s' callback: %s", self._attr_name, e
                )
                # Notify the user through persistent notification
                try:
                    await self.hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": f"Pool Control - Erreur Bouton {self._attr_name}",
                            "message": f"Une erreur s'est produite lors de l'exécution du bouton {self._attr_name}: {e}",
                            "notification_id": f"pool_control_button_error_{self._attr_unique_id}",
                        },
                        blocking=False,
                    )
                except Exception as notify_error:
                    _LOGGER.error("Failed to send notification: %s", notify_error)
