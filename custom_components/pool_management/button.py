"""Button platform for Pool Management integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entities import PoolManagementButton


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Management buttons."""

    domain_data = hass.data[DOMAIN]
    controller = (
        domain_data[entry.entry_id] if isinstance(domain_data, dict) else domain_data
    )

    entities = [
        PoolManagementButton(
            controller,
            "reset",
            "pool_management_reset",
            controller.executeButtonReset,
            entry=entry,
        ),
        PoolManagementButton(
            controller,
            "stop",
            "pool_management_stop",
            controller.executeButtonStop,
            entry=entry,
        ),
        PoolManagementButton(
            controller,
            "booster",
            "pool_management_surpresseur",
            controller.executeSurpresseurOn,
            entry=entry,
        ),
        PoolManagementButton(
            controller,
            "backwash",
            "pool_management_lavage",
            controller.executeFiltreSableLavageOn,
            entry=entry,
        ),
        PoolManagementButton(
            controller,
            "active",
            "pool_management_actif",
            controller.executeButtonActif,
            entry=entry,
        ),
        PoolManagementButton(
            controller,
            "auto",
            "pool_management_auto",
            controller.executeButtonAuto,
            entry=entry,
        ),
        PoolManagementButton(
            controller,
            "inactive",
            "pool_management_inactif",
            controller.executeButtonInactif,
            entry=entry,
        ),
        PoolManagementButton(
            controller,
            "winter",
            "pool_management_hivernage",
            controller.executeButtonHivernage,
            entry=entry,
        ),
        PoolManagementButton(
            controller,
            "season",
            "pool_management_saison",
            controller.executeButtonSaison,
            entry=entry,
        ),
    ]

    async_add_entities(entities)
