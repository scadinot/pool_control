"""Pool Control integration sensors."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entities import PoolControlStatusSensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pool Control sensors."""

    controller = hass.data[DOMAIN]

    entities = [
        PoolControlStatusSensor(
            controller,
            "Status Asservissement",
            "pool_control_asservissement_status",
            "asservissementStatus",
            default_state="",
        ),
        PoolControlStatusSensor(
            controller,
            "Temps de filtration",
            "pool_control_filtration_time",
            "filtrationTimeStatus",
            default_state="",
        ),
        PoolControlStatusSensor(
            controller,
            "Planning de Filtration",
            "pool_control_filtration_schedule",
            "filtrationScheduleStatus",
            default_state="",
        ),
        PoolControlStatusSensor(
            controller,
            "Status Filtration",
            "pool_control_filtration_status",
            "filtrationStatus",
        ),
        PoolControlStatusSensor(
            controller,
            "Status Surpresseur",
            "pool_control_surpresseur_status",
            "surpresseurStatus",
        ),
        PoolControlStatusSensor(
            controller,
            "Status Lavage Filtre",
            "pool_control_filtre_sable_lavage_status",
            "filtreSableLavageStatus",
        ),
    ]

    async_add_entities(entities)
