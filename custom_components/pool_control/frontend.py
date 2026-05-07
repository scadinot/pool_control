"""Frontend panel registration for Pool Control.

Sert le fichier JS du panneau via l'URL statique
``/pool_control_static/`` et enregistre l'entrée latérale.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.core import HomeAssistant

try:
    # HA ≥ 2024.7 — API moderne pour servir des fichiers statiques.
    from homeassistant.components.http import StaticPathConfig
except ImportError:  # pragma: no cover - compat older HA
    StaticPathConfig = None

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = "pool-control"            # → /pool-control dans l'URL
PANEL_TITLE = "Pool Control"
PANEL_ICON = "mdi:pool"
PANEL_NAME = "pool-control-panel"          # nom du Web Component

STATIC_PATH = "/pool_control_static"       # URL servie par HA
JS_FILENAME = "pool_control_panel.js"


async def async_register_panel(hass: HomeAssistant, config_entry_data: dict) -> None:
    """Enregistre le panneau latéral et sert le fichier JS.

    À appeler depuis ``async_setup_entry`` dans ``__init__.py``.

    Le ``config_entry_data`` est transmis au Web Component via
    ``panel.config`` ; on y passe les options utilisateur (entité eau,
    entité air, préfixe d'instance).
    """
    # 1. Servir le dossier statique (une seule fois)
    if STATIC_PATH not in hass.data.get("pool_control_static_registered", set()):
        frontend_dir = Path(__file__).parent / "frontend"
        if StaticPathConfig is not None:
            await hass.http.async_register_static_paths(
                [StaticPathConfig(STATIC_PATH, str(frontend_dir), cache_headers=False)]
            )
        else:  # pragma: no cover - compat older HA (< 2024.7)
            hass.http.register_static_path(STATIC_PATH, str(frontend_dir), cache_headers=False)
        hass.data.setdefault("pool_control_static_registered", set()).add(STATIC_PATH)
        _LOGGER.info("Pool Control: static path %s mounted on %s", STATIC_PATH, frontend_dir)

    # 2. Enregistrer le panneau latéral (idempotent)
    if PANEL_URL_PATH in hass.data.get(frontend.DATA_PANELS, {}):
        _LOGGER.debug("Pool Control panel already registered, skipping")
        return

    # Configuration transmise au Web Component via panel.config.
    # Les clés du config_flow Pool Control sont en camelCase
    # (temperatureWater, temperatureOutdoor) ; on les remappe vers les
    # noms attendus par le Web Component.
    panel_config = {
        "instance_prefix": config_entry_data.get("instance_prefix", "pool_control"),
        "water_entity": config_entry_data.get("temperatureWater"),
        "air_entity": config_entry_data.get("temperatureOutdoor"),
    }

    await panel_custom.async_register_panel(
        hass=hass,
        webcomponent_name=PANEL_NAME,
        frontend_url_path=PANEL_URL_PATH,
        module_url=f"{STATIC_PATH}/{JS_FILENAME}",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        config=panel_config,
        require_admin=False,
        embed_iframe=False,
    )
    _LOGGER.info("Pool Control panel registered at /%s", PANEL_URL_PATH)


async def async_unregister_panel(hass: HomeAssistant) -> None:
    """Retire le panneau latéral (à appeler depuis async_unload_entry)."""
    if PANEL_URL_PATH in hass.data.get(frontend.DATA_PANELS, {}):
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
        _LOGGER.info("Pool Control panel unregistered")
