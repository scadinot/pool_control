"""Tests pour l'enregistrement du panneau frontend."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components import frontend

from custom_components.pool_control.frontend import (
    PANEL_NAME,
    PANEL_URL_PATH,
    async_register_panel,
    async_unregister_panel,
)


@pytest.fixture
def hass():
    """Mock minimal d'une instance Home Assistant pour les tests panel."""

    instance = MagicMock()
    instance.data = {}
    instance.http = MagicMock()
    instance.http.async_register_static_paths = AsyncMock()
    return instance


async def test_register_panel(hass):
    """Le panneau s'enregistre avec la config attendue (clés HA mappées)."""

    with patch(
        "custom_components.pool_control.frontend.panel_custom.async_register_panel",
        new=AsyncMock(),
    ) as mock_register:
        await async_register_panel(
            hass,
            {
                "instance_prefix": "piscine",
                "temperatureWater": "sensor.water",
                "temperatureOutdoor": "sensor.air",
            },
        )

    mock_register.assert_called_once()
    kwargs = mock_register.call_args.kwargs
    assert kwargs["webcomponent_name"] == PANEL_NAME
    assert kwargs["frontend_url_path"] == PANEL_URL_PATH
    assert kwargs["config"]["instance_prefix"] == "piscine"
    assert kwargs["config"]["water_entity"] == "sensor.water"
    assert kwargs["config"]["air_entity"] == "sensor.air"


async def test_register_panel_idempotent(hass):
    """Un second appel ne ré-enregistre pas le panneau."""

    with patch(
        "custom_components.pool_control.frontend.panel_custom.async_register_panel",
        new=AsyncMock(),
    ) as mock_register:
        await async_register_panel(hass, {})
        # HA marque le panneau comme déjà enregistré
        hass.data.setdefault(frontend.DATA_PANELS, {})[PANEL_URL_PATH] = object()
        await async_register_panel(hass, {})

    assert mock_register.call_count == 1


async def test_unregister_panel(hass):
    """Le panneau est retiré quand l'intégration est déchargée."""

    hass.data.setdefault(frontend.DATA_PANELS, {})[PANEL_URL_PATH] = object()

    with patch(
        "custom_components.pool_control.frontend.frontend.async_remove_panel",
    ) as mock_remove:
        await async_unregister_panel(hass)

    mock_remove.assert_called_once_with(hass, PANEL_URL_PATH)


async def test_unregister_panel_when_absent(hass):
    """Pas d'erreur si le panneau n'était pas enregistré."""

    with patch(
        "custom_components.pool_control.frontend.frontend.async_remove_panel",
    ) as mock_remove:
        await async_unregister_panel(hass)

    mock_remove.assert_not_called()
