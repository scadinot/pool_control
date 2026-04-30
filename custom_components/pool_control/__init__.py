"""Integration for Pool Control."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.util import slugify

from .const import DOMAIN
from .controller import STORAGE_KEY, STORAGE_KEY_PREFIX, STORAGE_VERSION, PoolController

PLATFORMS = ["sensor", "button"]
_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrer les anciennes config entries vers le format multi-instance."""

    _LOGGER.info(
        "Migrating Pool Control entry %s from version %s",
        entry.entry_id,
        entry.version,
    )

    if entry.version == 1:
        # Préserver le titre existant comme nom d'instance
        name = entry.data.get("name") or entry.title or "Pool Control"
        new_data = {**entry.data, "name": name}

        # Récupérer l'unique_id basé sur le nom (compatible Shutters Management)
        new_unique_id = slugify(name)

        # Migrer les données du Store : ancienne clé globale → clé par entry
        legacy_store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        legacy_data = await legacy_store.async_load()
        if legacy_data:
            new_store = Store(
                hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{entry.entry_id}"
            )
            await new_store.async_save(legacy_data)
            await legacy_store.async_remove()
            _LOGGER.info(
                "Migrated %d storage keys from %s to per-entry store",
                len(legacy_data),
                STORAGE_KEY,
            )

        # Préserver les entités déjà enregistrées : préfixer leur unique_id
        # avec entry_id pour les aligner sur le nouveau format multi-instance
        # sans perdre les customisations du registre.
        entity_registry = er.async_get(hass)
        for ent in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
            new_uid = f"{entry.entry_id}_{ent.unique_id}"
            if ent.unique_id != new_uid and not ent.unique_id.startswith(
                f"{entry.entry_id}_"
            ):
                entity_registry.async_update_entity(
                    ent.entity_id, new_unique_id=new_uid
                )

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            unique_id=new_unique_id,
            version=2,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Installer Pool Control à partir d'un config entry."""

    _LOGGER.info("Setting up Pool Control from Config Entry %s", entry.title)

    conf = {**entry.data, **entry.options}

    controller = PoolController(hass, conf, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller

    await controller.async_initialize()

    # Démarrer les plateformes déclarées (sensor.py, button.py seront appelés ici)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Ensuite on peut lancer le cron
    await controller.startFirstCron()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger Pool Control."""

    _LOGGER.info("Unloading Pool Control %s", entry.title)

    # Arrêter les crons avant de décharger les plateformes
    controller = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if controller is not None:
        await controller.stopFirstCron()
        await controller.stopSecondCron()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if not hass.data.get(DOMAIN):
            hass.data.pop(DOMAIN, None)

    return unload_ok
