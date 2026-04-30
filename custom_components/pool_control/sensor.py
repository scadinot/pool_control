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

    domain_data = hass.data[DOMAIN]
    controller = (
        domain_data[entry.entry_id] if isinstance(domain_data, dict) else domain_data
    )

    entities = [
        PoolControlStatusSensor(
            controller,
            "Status Asservissement",
            "pool_control_asservissement_status",
            "asservissementStatus",
            default_state="",
            entry=entry,
        ),
        PoolControlStatusSensor(
            controller,
            "Temps de filtration",
            "pool_control_filtration_time",
            "filtrationTimeStatus",
            default_state="",
            entry=entry,
        ),
        PoolControlStatusSensor(
            controller,
            "Planning de Filtration",
            "pool_control_filtration_schedule",
            "filtrationScheduleStatus",
            default_state="",
            entry=entry,
        ),
        PoolControlStatusSensor(
            controller,
            "Status Filtration",
            "pool_control_filtration_status",
            "filtrationStatus",
            entry=entry,
        ),
        PoolControlStatusSensor(
            controller,
            "Status Surpresseur",
            "pool_control_surpresseur_status",
            "surpresseurStatus",
            entry=entry,
        ),
        PoolControlStatusSensor(
            controller,
            "Status Lavage Filtre",
            "pool_control_filtre_sable_lavage_status",
            "filtreSableLavageStatus",
            entry=entry,
        ),
    ]

    async_add_entities(entities)
