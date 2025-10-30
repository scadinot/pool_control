"""Integration for Pool Control."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .controller import PoolController
from .options_flow import PoolControlOptionsFlowHandler

PLATFORMS = ["sensor", "button"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Installer Pool Control à partir d'un config entry."""

    _LOGGER.info("Setting up Pool Control from Config Entry")

    conf = {**entry.data, **entry.options}

    controller = PoolController(hass, conf)
    hass.data.setdefault(DOMAIN, controller)

    await controller.async_initialize()

    # Démarrer les plateformes déclarées (sensor.py, button.py seront appelés ici)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Ensuite on peut lancer le cron
    await controller.startFirstCron()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger Pool Control."""

    _LOGGER.info("Unloading Pool Control")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data.pop(DOMAIN, None)

    return unload_ok


async def async_get_options_flow(config_entry):
    """Retourne le flow d'options."""

    return PoolControlOptionsFlowHandler(config_entry)
