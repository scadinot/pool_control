"""Entities for Pool Control integration."""

from typing import Any, Callable, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


def _build_device_info(entry: Optional[ConfigEntry]) -> Optional[DeviceInfo]:
    """Build the DeviceInfo grouping all entities of a given config entry."""

    if entry is None:
        return None

    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Pool Control",
        entry_type=DeviceEntryType.SERVICE,
    )


class PoolControlStatusSensor(SensorEntity):
    """Sensor générique pour afficher un statut Pool Control."""

    _attr_has_entity_name = True

    def __init__(
        self,
        controller: Any,
        translation_key: str,
        unique_id: str,
        controller_attribute_name: str,
        default_state: str = "Arrêté",
        entry: Optional[ConfigEntry] = None,
    ) -> None:
        """Initialize the PoolControlStatusSensor."""

        self._controller = controller
        self._attr_translation_key = translation_key
        self._attr_unique_id = (
            f"{entry.entry_id}_{unique_id}" if entry is not None else unique_id
        )
        self._attr_device_info = _build_device_info(entry)
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

    _attr_has_entity_name = True

    def __init__(
        self,
        controller: Any,
        translation_key: str,
        unique_id: str,
        callback: Callable,
        entry: Optional[ConfigEntry] = None,
    ) -> None:
        """Initialize the PoolControlButton."""

        self._controller = controller
        self._attr_translation_key = translation_key
        self._attr_unique_id = (
            f"{entry.entry_id}_{unique_id}" if entry is not None else unique_id
        )
        self._attr_device_info = _build_device_info(entry)
        self._callback = callback

    async def async_press(self) -> None:
        """Handle the button press."""

        if self._callback:
            await self._callback()
