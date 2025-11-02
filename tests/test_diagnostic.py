"""Test minimal pour diagnostiquer les problèmes GitHub Actions."""

import pytest
import asyncio


def test_basic_import():
    """Test que pytest fonctionne."""
    assert True


def test_homeassistant_available():
    """Test que Home Assistant est installé."""
    try:
        import homeassistant
        assert True, "Home Assistant is installed"
    except ImportError:
        pytest.skip("Home Assistant not installed")


def test_custom_component_import():
    """Test que le custom component peut être importé."""
    try:
        import homeassistant  # Doit être importé d'abord
        from custom_components.pool_control import const
        assert const.DOMAIN == "pool_control"
    except ImportError as e:
        pytest.skip(f"Cannot import: {e}")


@pytest.mark.asyncio
async def test_async_works():
    """Test que pytest-asyncio fonctionne."""
    await asyncio.sleep(0.001)
    assert True


if __name__ == "__main__":
    import asyncio
    pytest.main([__file__, "-v"])
