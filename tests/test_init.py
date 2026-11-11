"""Tests du module d'installation : application des options et nettoyage.

Le contrôleur recopie chaque réglage dans un attribut à sa construction et
ne relit jamais la configuration ensuite. Une option modifiée n'atteint donc
le contrôleur que si l'entrée est rechargée — d'où le listener vérifié ici.
Rafraîchir le seul panneau, comme le faisait la version précédente, laissait
le contrôleur sur ses anciennes valeurs jusqu'au prochain redémarrage.

Le second défaut couvert est plus discret. Le contrôleur s'abonne à
l'extinction de Home Assistant pour sauvegarder son état ; tant que cet
abonnement n'est pas annulé au déchargement, chaque rechargement laisse
derrière lui un contrôleur toujours abonné, avec son état figé et son Store
sur la même clé. À l'extinction, le dernier qui écrit gagne : un contrôleur
fantôme peut réécrire un état périmé et faire repasser l'hivernage en
saison, désarmant la protection hors-gel.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from custom_components.pool_management import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.pool_management.const import DOMAIN
from custom_components.pool_management.controller import PoolController

MODULE = "custom_components.pool_management"


def _hass() -> MagicMock:
    """Home Assistant réduit à ce que l'installation lui demande."""

    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_reload = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    return hass


def _entry(data: dict | None = None, options: dict | None = None) -> MagicMock:
    """Config entry minimale, dont on observe les abonnements."""

    entry = MagicMock()
    entry.entry_id = "entry-1"
    entry.title = "Piscine"
    entry.unique_id = "piscine"
    entry.data = data if data is not None else {"name": "Piscine"}
    entry.options = options if options is not None else {}
    entry.add_update_listener = Mock(return_value=Mock())
    entry.async_on_unload = Mock()
    return entry


def _controller() -> MagicMock:
    """Contrôleur factice : seules les méthodes attendues sont asynchrones."""

    controller = MagicMock()
    controller.async_initialize = AsyncMock()
    controller.startFirstCron = AsyncMock()
    controller.resumeSecondCron = AsyncMock()
    controller.stopFirstCron = AsyncMock()
    controller.stopSecondCron = AsyncMock()
    return controller


@pytest.mark.bugs
async def test_modifier_les_options_recharge_l_entree():
    """Le listener d'options doit recharger l'entrée.

    Régression : le listener ne rafraîchissait que le panneau, de sorte
    qu'un réglage modifié n'était appliqué qu'au redémarrage suivant.
    """

    hass, entry = _hass(), _entry()

    with (
        patch(f"{MODULE}.PoolController", return_value=_controller()),
        patch(f"{MODULE}.async_register_panel", new=AsyncMock()),
        patch(f"{MODULE}.async_unregister_panel", new=AsyncMock()),
    ):
        assert await async_setup_entry(hass, entry) is True

        entry.add_update_listener.assert_called_once()
        listener = entry.add_update_listener.call_args[0][0]

        await listener(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with(entry.entry_id)


@pytest.mark.bugs
async def test_decharger_annule_l_abonnement_a_l_extinction():
    """Le déchargement doit détacher l'abonnement à l'extinction.

    Sans cela, chaque rechargement laisse un contrôleur fantôme capable
    de réécrire un état périmé sur la même clé de Store.
    """

    hass, entry = _hass(), _entry()
    controller = _controller()
    hass.data[DOMAIN] = {entry.entry_id: controller}

    with patch(f"{MODULE}.async_unregister_panel", new=AsyncMock()):
        assert await async_unload_entry(hass, entry) is True

    controller.detach_stop_listener.assert_called_once()


@pytest.mark.bugs
async def test_le_controleur_sait_detacher_son_abonnement():
    """Le contrôleur conserve le handle rendu par le bus et l'annule.

    Le test précédent s'appuie sur un contrôleur factice : celui-ci
    vérifie que la méthode existe réellement et annule le bon handle.
    """

    hass = _hass()
    desabonnement = Mock()
    hass.bus = MagicMock()
    hass.bus.async_listen_once = Mock(return_value=desabonnement)

    with patch("custom_components.pool_management.controller.Store") as store:
        store.return_value.async_load = AsyncMock(return_value=None)
        controller = PoolController(hass, {}, _entry())
        await controller.async_initialize()

    hass.bus.async_listen_once.assert_called_once()
    desabonnement.assert_not_called()

    controller.detach_stop_listener()

    desabonnement.assert_called_once()


async def test_detacher_deux_fois_est_sans_effet():
    """Un second détachement ne doit pas rappeler le désabonnement."""

    hass = _hass()
    desabonnement = Mock()
    hass.bus = MagicMock()
    hass.bus.async_listen_once = Mock(return_value=desabonnement)

    with patch("custom_components.pool_management.controller.Store") as store:
        store.return_value.async_load = AsyncMock(return_value=None)
        controller = PoolController(hass, {}, _entry())
        await controller.async_initialize()

    controller.detach_stop_listener()
    controller.detach_stop_listener()

    desabonnement.assert_called_once()


async def test_detacher_sans_initialisation_est_sans_effet():
    """Une entrée qui n'a jamais démarré se décharge sans erreur."""

    hass = _hass()

    with patch("custom_components.pool_management.controller.Store"):
        controller = PoolController(hass, {}, _entry())

    controller.detach_stop_listener()


async def test_les_options_priment_sur_les_donnees_initiales():
    """Le contrôleur est construit sur les options, pas sur les données d'origine.

    Test de contrôle : c'est cette fusion qui donne son effet au
    rechargement, le réglage modifié vivant dans les options.
    """

    hass = _hass()
    entry = _entry(
        data={"name": "Piscine", "datePivot": "13:00"},
        options={"datePivot": "09:00"},
    )

    with (
        patch(f"{MODULE}.PoolController", return_value=_controller()) as classe,
        patch(f"{MODULE}.async_register_panel", new=AsyncMock()),
    ):
        await async_setup_entry(hass, entry)

    config = classe.call_args[0][1]
    assert config["datePivot"] == "09:00"
