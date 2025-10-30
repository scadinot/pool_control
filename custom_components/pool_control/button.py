"""Button platform for Pool Control integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entities import PoolControlButton


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Control buttons."""

    controller = hass.data[DOMAIN]

    entities = [
        PoolControlButton(
            controller, "Reset", "pool_control_reset", controller.executeButtonReset
        ),
        PoolControlButton(
            controller, "Stop", "pool_control_stop", controller.executeButtonStop
        ),
        PoolControlButton(
            controller,
            "Surpresseur",
            "pool_control_surpresseur",
            controller.executeSurpresseurOn,
        ),
        PoolControlButton(
            controller,
            "Lavage",
            "pool_control_lavage",
            controller.executeFiltreSableLavageOn,
        ),
        PoolControlButton(
            controller, "Actif", "pool_control_actif", controller.executeButtonActif
        ),
        PoolControlButton(
            controller, "Auto", "pool_control_auto", controller.executeButtonAuto
        ),
        PoolControlButton(
            controller,
            "Inactif",
            "pool_control_inactif",
            controller.executeButtonInactif,
        ),
        PoolControlButton(
            controller,
            "Hivernage",
            "pool_control_hivernage",
            controller.executeButtonHivernage,
        ),
        PoolControlButton(
            controller, "Saison", "pool_control_saison", controller.executeButtonSaison
        ),
    ]

    async_add_entities(entities)
