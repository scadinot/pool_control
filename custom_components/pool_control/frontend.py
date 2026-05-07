"""Frontend panel registration for Pool Control.

Sert le fichier JS du panneau via l'URL statique
``/pool_control_static/`` et enregistre une entrée latérale **par
instance** afin de ne pas entrer en collision quand plusieurs piscines
cohabitent.
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

PANEL_BASE_URL_PATH = "pool-control"        # URL pour l'instance par défaut
PANEL_TITLE = "Pool Control"
PANEL_ICON = "mdi:pool"
PANEL_NAME = "pool-control-panel"          # nom du Web Component

STATIC_PATH = "/pool_control_static"       # URL servie par HA
JS_FILENAME = "pool_control_panel.js"

DEFAULT_SLUG = "pool_control"


def _panel_url_path(slug: str) -> str:
    """Build a per-instance URL path.

    - L'instance par défaut (``pool_control``) garde l'URL historique
      ``pool-control`` pour préserver d'éventuels bookmarks utilisateurs.
    - Les autres instances reçoivent un suffixe dérivé de leur slug
      (``pool-control-piscine``, ``pool-control-spa``, …) afin que
      chaque ConfigEntry dispose de sa propre entrée de sidebar et de
      son propre URL.
    """

    if not slug or slug == DEFAULT_SLUG:
        return PANEL_BASE_URL_PATH
    return f"{PANEL_BASE_URL_PATH}-{slug.replace('_', '-')}"


def _sidebar_title(slug: str, entry_title: str | None) -> str:
    """Disambiguate the sidebar title in multi-instance setups."""

    if not slug or slug == DEFAULT_SLUG:
        return PANEL_TITLE
    return f"{PANEL_TITLE} · {entry_title}" if entry_title else PANEL_TITLE


async def async_register_panel(
    hass: HomeAssistant,
    slug: str,
    entry_title: str | None,
    config_entry_data: dict,
) -> None:
    """Enregistre une entrée de sidebar pour cette instance.

    À appeler depuis ``async_setup_entry`` dans ``__init__.py``. Chaque
    instance reçoit une URL et un titre distincts pour pouvoir cohabiter
    avec d'autres instances Pool Control.

    Le ``config_entry_data`` est transmis au Web Component via
    ``panel.config`` ; on y passe l'``instance_prefix`` (slug) ainsi que
    les entités de température configurées par l'utilisateur.
    """

    # 1. Servir le dossier statique (une seule fois pour le domaine)
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

    url_path = _panel_url_path(slug)

    # 2. Enregistrer le panneau pour cette instance (idempotent)
    if url_path in hass.data.get(frontend.DATA_PANELS, {}):
        _LOGGER.debug(
            "Pool Control panel already registered at /%s, skipping", url_path
        )
        return

    # Configuration transmise au Web Component via panel.config.
    # Les clés du config_flow Pool Control sont en camelCase
    # (temperatureWater, temperatureOutdoor) ; on les remappe vers les
    # noms attendus par le Web Component.
    panel_config = {
        "instance_prefix": slug or DEFAULT_SLUG,
        "water_entity": config_entry_data.get("temperatureWater"),
        "air_entity": config_entry_data.get("temperatureOutdoor"),
    }

    await panel_custom.async_register_panel(
        hass=hass,
        webcomponent_name=PANEL_NAME,
        frontend_url_path=url_path,
        module_url=f"{STATIC_PATH}/{JS_FILENAME}",
        sidebar_title=_sidebar_title(slug, entry_title),
        sidebar_icon=PANEL_ICON,
        config=panel_config,
        require_admin=False,
        embed_iframe=False,
    )
    _LOGGER.info("Pool Control panel registered at /%s", url_path)


async def async_unregister_panel(hass: HomeAssistant, slug: str) -> None:
    """Retire uniquement le panneau de cette instance.

    À appeler depuis ``async_unload_entry``. Les autres instances
    Pool Control encore actives conservent leur entrée de sidebar.
    """

    url_path = _panel_url_path(slug)
    if url_path in hass.data.get(frontend.DATA_PANELS, {}):
        frontend.async_remove_panel(hass, url_path)
        _LOGGER.info("Pool Control panel unregistered (/%s)", url_path)
