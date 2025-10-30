"""Entities for Pool Control integration."""

from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorEntity


class PoolControlStatusSensor(SensorEntity):
    """Sensor générique pour afficher un statut Pool Control."""

    def __init__(
        self,
        controller,
        name,
        unique_id,
        controller_attribute_name,
        default_state="Arrêté",
    ):
        """Initialize the PoolControlStatusSensor."""

        self._controller = controller
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._controller_attribute_name = controller_attribute_name
        self._state = default_state
        self._ready = False

        # Dès la création, on attache l'entité au controller dynamiquement
        setattr(controller, controller_attribute_name, self)

    async def async_added_to_hass(self):
        """Call when the entity is added to hass."""

        self._ready = True

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._state

    def set_status(self, value):
        """Set the status of the sensor."""

        self._state = value
        if self._ready:
            self.async_write_ha_state()


class PoolControlButton(ButtonEntity):
    """Button générique pour Pool Control."""

    def __init__(self, controller, name, unique_id, callback):
        """Initialize the PoolControlButton."""

        self._controller = controller
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._callback = callback

    async def async_press(self) -> None:
        """Handle the button press."""

        if self._callback:
            await self._callback()
