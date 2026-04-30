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

    domain_data = hass.data[DOMAIN]
    controller = (
        domain_data[entry.entry_id] if isinstance(domain_data, dict) else domain_data
    )

    entities = [
        PoolControlButton(
            controller,
            "reset",
            "pool_control_reset",
            controller.executeButtonReset,
            entry=entry,
        ),
        PoolControlButton(
            controller,
            "stop",
            "pool_control_stop",
            controller.executeButtonStop,
            entry=entry,
        ),
        PoolControlButton(
            controller,
            "booster",
            "pool_control_surpresseur",
            controller.executeSurpresseurOn,
            entry=entry,
        ),
        PoolControlButton(
            controller,
            "backwash",
            "pool_control_lavage",
            controller.executeFiltreSableLavageOn,
            entry=entry,
        ),
        PoolControlButton(
            controller,
            "active",
            "pool_control_actif",
            controller.executeButtonActif,
            entry=entry,
        ),
        PoolControlButton(
            controller,
            "auto",
            "pool_control_auto",
            controller.executeButtonAuto,
            entry=entry,
        ),
        PoolControlButton(
            controller,
            "inactive",
            "pool_control_inactif",
            controller.executeButtonInactif,
            entry=entry,
        ),
        PoolControlButton(
            controller,
            "winter",
            "pool_control_hivernage",
            controller.executeButtonHivernage,
            entry=entry,
        ),
        PoolControlButton(
            controller,
            "season",
            "pool_control_saison",
            controller.executeButtonSaison,
            entry=entry,
        ),
    ]

    async_add_entities(entities)
