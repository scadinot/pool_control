"""Tests for pool_control entity helpers."""
from unittest.mock import MagicMock

import pytest

from custom_components.pool_control.entities import _build_suggested_object_id


class TestBuildSuggestedObjectId:
    """Coverage for the language-agnostic object_id helper."""

    def test_returns_none_when_entry_is_none(self):
        """Without a ConfigEntry there is nothing to anchor a prefix on."""

        assert _build_suggested_object_id(None, "active") is None

    def test_uses_entry_unique_id_when_set(self):
        """unique_id is the stable slug computed at config flow time."""

        entry = MagicMock(unique_id="pool_control", title="Pool Control")

        result = _build_suggested_object_id(entry, "active")

        assert result == "pool_control_active"

    def test_unique_id_remains_after_title_rename(self):
        """Renaming the entry must not shift the prefix used for new entities."""

        entry = MagicMock(unique_id="pool_control", title="Renamed By User")

        result = _build_suggested_object_id(entry, "filtration_time")

        assert result == "pool_control_filtration_time"

    @pytest.mark.parametrize("falsy", [None, ""])
    def test_falls_back_to_slugified_title_when_no_unique_id(self, falsy):
        """Legacy entries without a unique_id fall back to the title slug."""

        entry = MagicMock(unique_id=falsy, title="Ma Piscine")

        result = _build_suggested_object_id(entry, "booster_status")

        assert result == "ma_piscine_booster_status"
