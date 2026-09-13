"""Tests for pool_control entity helpers."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import State

from custom_components.pool_control.entities import (
    PoolControlStatusSensor,
    _build_entity_id,
)


def _make_sensor(restore_state=True, default_state=""):
    """Build a filtration schedule sensor attached to a mock controller."""

    entry = MagicMock(entry_id="entry_id", unique_id="piscine", title="Piscine")
    return PoolControlStatusSensor(
        MagicMock(),
        "filtration_schedule",
        "pool_control_filtration_schedule",
        "filtrationScheduleStatus",
        default_state=default_state,
        entry=entry,
        restore_state=restore_state,
    )


def _last_state(value):
    """Patch async_get_last_state to return the given state (or None)."""

    state = None if value is None else State("sensor.piscine_filtration_schedule", value)
    return patch.object(
        PoolControlStatusSensor,
        "async_get_last_state",
        AsyncMock(return_value=state),
    )


class TestPoolControlStatusSensorRestore:
    """Restoration of the last known status after a restart."""

    async def test_restores_last_state(self):
        """The schedule is displayed again instead of staying empty until 19:32."""

        sensor = _make_sensor()

        with _last_state("09:44-19:32 : 25.6°C"):
            await sensor.async_added_to_hass()

        assert sensor.state == "09:44-19:32 : 25.6°C"

    @pytest.mark.parametrize("unusable", ["unknown", "unavailable", None])
    async def test_keeps_default_without_usable_last_state(self, unusable):
        """unknown / unavailable / no history keep the default state."""

        sensor = _make_sensor()

        with _last_state(unusable):
            await sensor.async_added_to_hass()

        assert sensor.state == ""

    async def test_does_not_restore_when_disabled(self):
        """Sensors created without restore_state keep their default state."""

        sensor = _make_sensor(restore_state=False, default_state="Arrêté")

        with _last_state("Actif : 03:12") as get_last_state:
            await sensor.async_added_to_hass()

        get_last_state.assert_not_called()
        assert sensor.state == "Arrêté"

    async def test_status_set_by_controller_takes_precedence(self):
        """A status provided before the entity is added is not overwritten."""

        sensor = _make_sensor()
        sensor.set_status("10:00-16:00 : 12.0°C")

        with _last_state("09:44-19:32 : 25.6°C"):
            await sensor.async_added_to_hass()

        assert sensor.state == "10:00-16:00 : 12.0°C"

    async def test_set_status_writes_state_once_added(self):
        """set_status writes the HA state only after the entity is added."""

        sensor = _make_sensor()
        sensor.async_write_ha_state = MagicMock()

        sensor.set_status("avant")
        sensor.async_write_ha_state.assert_not_called()

        with _last_state(None):
            await sensor.async_added_to_hass()

        sensor.set_status("après")
        sensor.async_write_ha_state.assert_called_once()
        assert sensor.state == "après"


class TestSensorPlatformRestore:
    """Which status sensors restore their state."""

    async def test_only_non_timer_statuses_restore(self):
        """Booster and backwash are rebuilt from the persisted cycle instead."""

        from custom_components.pool_control.sensor import async_setup_entry

        hass = MagicMock()
        hass.data = {"pool_control": {"entry_id": MagicMock()}}
        entry = MagicMock(entry_id="entry_id", unique_id="piscine", title="Piscine")
        added = []

        await async_setup_entry(hass, entry, added.extend)

        assert {sensor.translation_key: sensor._restore_state for sensor in added} == {
            "control_status": True,
            "filtration_time": True,
            "filtration_schedule": True,
            "filtration_status": True,
            "booster_status": False,
            "backwash_status": False,
        }


class TestBuildEntityId:
    """Coverage for the language-agnostic entity_id helper."""

    def test_returns_none_when_entry_is_none(self):
        """Without a ConfigEntry there is nothing to anchor a prefix on."""

        assert _build_entity_id("button", None, "active") is None

    def test_uses_entry_unique_id_when_set(self):
        """unique_id is the stable slug computed at config flow time."""

        entry = MagicMock(unique_id="pool_control", title="Pool Control")

        result = _build_entity_id("button", entry, "active")

        assert result == "button.pool_control_active"

    def test_unique_id_remains_after_title_rename(self):
        """Renaming the entry must not shift the prefix used for new entities."""

        entry = MagicMock(unique_id="pool_control", title="Renamed By User")

        result = _build_entity_id("sensor", entry, "filtration_time")

        assert result == "sensor.pool_control_filtration_time"

    @pytest.mark.parametrize("falsy", [None, ""])
    def test_falls_back_to_slugified_title_when_no_unique_id(self, falsy):
        """Legacy entries without a unique_id fall back to the title slug."""

        entry = MagicMock(unique_id=falsy, title="Ma Piscine")

        result = _build_entity_id("sensor", entry, "booster_status")

        assert result == "sensor.ma_piscine_booster_status"

    def test_platform_prefix_is_respected(self):
        """The platform argument drives the final domain of the entity_id."""

        entry = MagicMock(unique_id="piscine", title="Piscine")

        assert _build_entity_id("button", entry, "stop") == "button.piscine_stop"
        assert (
            _build_entity_id("sensor", entry, "control_status")
            == "sensor.piscine_control_status"
        )
