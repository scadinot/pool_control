"""Entities for Pool Control integration."""

from typing import Any, Callable, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify

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


def _build_entity_id(
    platform: str, entry: Optional[ConfigEntry], translation_key: str
) -> Optional[str]:
    """Build a stable, language-agnostic entity_id.

    Home Assistant derives the default object_id from the translated entity
    name in the language active at creation time, which produces French
    identifiers like ``button.pool_control_actif`` when HA is in French —
    even though ``translation_key`` is "active". Setting
    ``self.entity_id`` directly in ``__init__`` is the documented way to
    force a stable slug (see ``entity_platform.py`` ``async_add_entities``
    contract).

    The per-instance prefix is taken from ``entry.unique_id`` (already a
    slug, set once at config flow time and never modified), with a
    fallback to ``slugify(entry.title)`` for legacy entries that may not
    have a unique_id yet. This keeps the prefix stable even if the user
    later renames the config entry through the UI.
    """

    if entry is None:
        return None

    prefix = entry.unique_id if entry.unique_id else slugify(entry.title)
    return f"{platform}.{prefix}_{translation_key}"


class PoolControlStatusSensor(SensorEntity, RestoreEntity):
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
        restore_state: bool = False,
    ) -> None:
        """Initialize the PoolControlStatusSensor."""

        self._controller = controller
        self._attr_translation_key = translation_key
        self._attr_unique_id = (
            f"{entry.entry_id}_{unique_id}" if entry is not None else unique_id
        )
        suggested = _build_entity_id("sensor", entry, translation_key)
        if suggested is not None:
            self.entity_id = suggested
        self._attr_device_info = _build_device_info(entry)
        self._controller_attribute_name = controller_attribute_name
        self._state = default_state
        self._ready = False
        self._restore_state = restore_state
        self._status_set = False

        # Dès la création, on attache l'entité au controller dynamiquement
        setattr(controller, controller_attribute_name, self)

    async def async_added_to_hass(self) -> None:
        """Call when the entity is added to hass."""

        await super().async_added_to_hass()

        # Reprendre le dernier état connu après un redémarrage : sans cela, un
        # statut recalculé seulement de temps en temps (planning, temps de
        # filtration) reste vide jusqu'au prochain calcul. Un statut déjà
        # fourni par le controller reste prioritaire.
        if self._restore_state and not self._status_set:
            last_state = await self.async_get_last_state()
            if last_state is not None and last_state.state not in (
                STATE_UNKNOWN,
                STATE_UNAVAILABLE,
            ):
                self._state = last_state.state

        self._ready = True

    @property
    def state(self) -> str:
        """Return the state of the sensor."""

        return self._state

    def set_status(self, value: str) -> None:
        """Set the status of the sensor."""

        self._state = value
        self._status_set = True
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
        suggested = _build_entity_id("button", entry, translation_key)
        if suggested is not None:
            self.entity_id = suggested
        self._attr_device_info = _build_device_info(entry)
        self._callback = callback

    async def async_press(self) -> None:
        """Handle the button press."""

        if self._callback:
            await self._callback()
