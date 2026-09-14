"""Tests pour l'enregistrement du panneau frontend."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components import frontend

from custom_components.pool_control.frontend import (
    PANEL_BASE_URL_PATH,
    PANEL_NAME,
    PANEL_TITLE,
    async_register_panel,
    async_unregister_panel,
)


@pytest.fixture
def panel_hass(mock_hass):
    """Étend ``mock_hass`` avec les attributs ``http`` requis par le frontend."""

    mock_hass.http = MagicMock()
    mock_hass.http.async_register_static_paths = AsyncMock()
    mock_hass.http.register_static_path = MagicMock()
    return mock_hass


async def test_register_panel_default_instance(panel_hass):
    """Le panneau par défaut s'enregistre sous /pool-control avec le titre de base."""

    with patch(
        "custom_components.pool_control.frontend.panel_custom.async_register_panel",
        new=AsyncMock(),
    ) as mock_register:
        await async_register_panel(
            panel_hass,
            "pool_control",
            "Pool Control",
            {
                "temperatureWater": "sensor.water",
                "temperatureOutdoor": "sensor.air",
            },
        )

    mock_register.assert_called_once()
    kwargs = mock_register.call_args.kwargs
    assert kwargs["webcomponent_name"] == PANEL_NAME
    assert kwargs["frontend_url_path"] == PANEL_BASE_URL_PATH
    assert kwargs["sidebar_title"] == PANEL_TITLE
    assert kwargs["config"]["instance_prefix"] == "pool_control"
    assert kwargs["config"]["water_entity"] == "sensor.water"
    assert kwargs["config"]["air_entity"] == "sensor.air"


async def test_register_panel_passes_equipment_configuration(panel_hass):
    """Le synoptique reçoit les relais, la PAC, son capteur de puissance et les durées."""

    with patch(
        "custom_components.pool_control.frontend.panel_custom.async_register_panel",
        new=AsyncMock(),
    ) as mock_register:
        await async_register_panel(
            panel_hass,
            "piscine",
            "Piscine",
            {
                "filtration": "switch.filtration",
                "traitement": "switch.traitement_chlore",
                "traitement_2": "switch.traitement_ph",
                "surpresseur": "switch.surpresseur",
                "heatPump": "climate.pac",
                "heatPumpPower": "sensor.pac_power",
                "lavageDuree": 3,
                "rincageDuree": 0,
            },
        )

    config = mock_register.call_args.kwargs["config"]
    assert config["filtration_entity"] == "switch.filtration"
    assert config["treatment_entity"] == "switch.traitement_chlore"
    assert config["treatment_2_entity"] == "switch.traitement_ph"
    assert config["booster_entity"] == "switch.surpresseur"
    assert config["heat_pump_entity"] == "climate.pac"
    assert config["heat_pump_power_entity"] == "sensor.pac_power"
    assert config["backwash_duration"] == 3
    assert config["rinse_duration"] == 0


async def test_register_panel_optional_equipment_defaults(panel_hass):
    """Sans équipement optionnel, les entités valent None et les durées 2 min."""

    with patch(
        "custom_components.pool_control.frontend.panel_custom.async_register_panel",
        new=AsyncMock(),
    ) as mock_register:
        await async_register_panel(panel_hass, "pool_control", "Pool Control", {})

    config = mock_register.call_args.kwargs["config"]
    assert config["treatment_2_entity"] is None
    assert config["heat_pump_entity"] is None
    assert config["heat_pump_power_entity"] is None
    assert config["backwash_duration"] == 2
    assert config["rinse_duration"] == 2


async def test_register_panel_per_instance_url_and_title(panel_hass):
    """Une 2ᵉ instance reçoit une URL et un titre disambiguïsés."""

    with patch(
        "custom_components.pool_control.frontend.panel_custom.async_register_panel",
        new=AsyncMock(),
    ) as mock_register:
        await async_register_panel(
            panel_hass,
            "piscine",
            "Piscine",
            {"temperatureWater": "sensor.w", "temperatureOutdoor": "sensor.a"},
        )

    kwargs = mock_register.call_args.kwargs
    assert kwargs["frontend_url_path"] == "pool-control-piscine"
    assert kwargs["sidebar_title"] == f"{PANEL_TITLE} · Piscine"
    assert kwargs["config"]["instance_prefix"] == "piscine"


async def test_register_panel_idempotent_per_url(panel_hass):
    """Un 2ᵉ appel pour la même instance ne ré-enregistre pas le panneau."""

    with patch(
        "custom_components.pool_control.frontend.panel_custom.async_register_panel",
        new=AsyncMock(),
    ) as mock_register:
        await async_register_panel(panel_hass, "pool_control", "Pool Control", {})
        # HA marque le panneau comme déjà enregistré
        panel_hass.data.setdefault(frontend.DATA_PANELS, {})[PANEL_BASE_URL_PATH] = object()
        await async_register_panel(panel_hass, "pool_control", "Pool Control", {})

    assert mock_register.call_count == 1


async def test_unregister_panel_targets_only_that_instance(panel_hass):
    """``async_unregister_panel`` ne retire que le panneau de l'instance demandée."""

    panel_hass.data.setdefault(frontend.DATA_PANELS, {})["pool-control"] = object()
    panel_hass.data[frontend.DATA_PANELS]["pool-control-spa"] = object()

    with patch(
        "custom_components.pool_control.frontend.frontend.async_remove_panel",
    ) as mock_remove:
        await async_unregister_panel(panel_hass, "spa")

    mock_remove.assert_called_once_with(panel_hass, "pool-control-spa")


async def test_unregister_panel_when_absent(panel_hass):
    """Pas d'erreur si le panneau n'était pas enregistré."""

    with patch(
        "custom_components.pool_control.frontend.frontend.async_remove_panel",
    ) as mock_remove:
        await async_unregister_panel(panel_hass, "pool_control")

    mock_remove.assert_not_called()
