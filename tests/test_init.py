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
    _async_reload_entry,
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
    controller.stop_replaced_relays = AsyncMock()
    controller.async_save_data = AsyncMock()
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


def _etat(valeur: str) -> MagicMock:
    """État Home Assistant réduit à sa valeur."""

    etat = MagicMock()
    etat.state = valeur
    return etat


def _controleur_reel(hass: MagicMock, config: dict) -> PoolController:
    """Vrai contrôleur, dont seuls le Store et les services sont simulés."""

    hass.services.async_call = AsyncMock()
    with patch("custom_components.pool_management.controller.Store"):
        return PoolController(hass, config, _entry())


@pytest.mark.bugs
async def test_un_relais_remplace_est_coupe_avant_le_rechargement():
    """Un actionneur actif retiré de la configuration doit être coupé.

    Régression : le contrôleur reconstruit ne connaît plus l'ancien
    identifiant. Un relais qu'on lui retire resterait allumé sans personne
    pour l'éteindre — une pompe doseuse orpheline doserait indéfiniment.
    """

    hass = _hass()
    hass.states.get = Mock(return_value=_etat("on"))
    controleur = _controleur_reel(hass, {"surpresseur": "switch.ancien"})

    await controleur.stop_replaced_relays({"surpresseur": "switch.nouveau"})

    hass.services.async_call.assert_awaited_once_with(
        "switch", "turn_off", {"entity_id": "switch.ancien"}
    )


@pytest.mark.bugs
async def test_la_filtration_est_coupee_en_dernier():
    """L'ordre d'arrêt doit protéger le matériel.

    L'eau doit circuler tant qu'un équipement tourne : traitements
    d'abord, surpresseur ensuite, filtration en dernier.
    """

    hass = _hass()
    hass.states.get = Mock(return_value=_etat("on"))
    controleur = _controleur_reel(
        hass,
        {
            "filtration": "switch.pompe",
            "traitement": "switch.chlore",
            "traitement_2": "switch.ph",
            "surpresseur": "switch.booster",
        },
    )

    # Configuration vide : tous les actionneurs sont retirés
    await controleur.stop_replaced_relays({})

    coupes = [
        appel.args[2]["entity_id"]
        for appel in hass.services.async_call.await_args_list
    ]
    assert coupes == [
        "switch.chlore",
        "switch.ph",
        "switch.booster",
        "switch.pompe",
    ]


async def test_un_relais_inchange_n_est_pas_coupe():
    """Un actionneur conservé ne doit pas être touché."""

    hass = _hass()
    hass.states.get = Mock(return_value=_etat("on"))
    config = {"surpresseur": "switch.booster", "filtration": "switch.pompe"}
    controleur = _controleur_reel(hass, config)

    await controleur.stop_replaced_relays(dict(config))

    hass.services.async_call.assert_not_awaited()


async def test_un_relais_deja_eteint_n_est_pas_commande():
    """Inutile de couper ce qui est déjà à l'arrêt."""

    hass = _hass()
    hass.states.get = Mock(return_value=_etat("off"))
    controleur = _controleur_reel(hass, {"surpresseur": "switch.ancien"})

    await controleur.stop_replaced_relays({"surpresseur": "switch.nouveau"})

    hass.services.async_call.assert_not_awaited()


async def test_un_relais_introuvable_n_est_pas_commande():
    """Une entité disparue du registre ne doit pas provoquer d'erreur."""

    hass = _hass()
    hass.states.get = Mock(return_value=None)
    controleur = _controleur_reel(hass, {"surpresseur": "switch.disparu"})

    await controleur.stop_replaced_relays({"surpresseur": "switch.nouveau"})

    hass.services.async_call.assert_not_awaited()


async def test_le_domaine_du_service_suit_l_entite():
    """Un ``input_boolean`` se coupe par son propre domaine."""

    hass = _hass()
    hass.states.get = Mock(return_value=_etat("on"))
    controleur = _controleur_reel(hass, {"traitement": "input_boolean.chlore"})

    await controleur.stop_replaced_relays({})

    hass.services.async_call.assert_awaited_once_with(
        "input_boolean", "turn_off", {"entity_id": "input_boolean.chlore"}
    )


@pytest.mark.bugs
async def test_le_rechargement_coupe_les_relais_retires_d_abord():
    """Les actionneurs orphelins doivent être coupés avant le rechargement.

    Une fois l'entrée rechargée, l'ancien contrôleur a disparu et
    l'identifiant du relais retiré avec lui.
    """

    hass = _hass()
    entry = _entry(options={"surpresseur": "switch.nouveau"})
    controller = _controller()
    hass.data[DOMAIN] = {entry.entry_id: controller}

    journal: list[str] = []
    controller.stop_replaced_relays = AsyncMock(
        side_effect=lambda config: journal.append("arret")
    )
    hass.config_entries.async_reload = AsyncMock(
        side_effect=lambda entry_id: journal.append("rechargement")
    )

    await _async_reload_entry(hass, entry)

    assert journal == ["arret", "rechargement"]
    config = controller.stop_replaced_relays.await_args[0][0]
    assert config["surpresseur"] == "switch.nouveau"


async def test_le_rechargement_fonctionne_sans_controleur():
    """Une entrée sans contrôleur en mémoire se recharge quand même."""

    hass, entry = _hass(), _entry()

    await _async_reload_entry(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with(entry.entry_id)


@pytest.mark.bugs
async def test_decharger_sauvegarde_l_etat_avant_reconstruction():
    """Le déchargement doit fixer l'état sur disque.

    ``set_data`` planifie ses sauvegardes en tâche de fond : une écriture
    encore en vol serait relue par le contrôleur reconstruit, qui
    repartirait d'un état périmé — un hivernage tout juste activé, par
    exemple.
    """

    hass, entry = _hass(), _entry()
    controller = _controller()
    hass.data[DOMAIN] = {entry.entry_id: controller}

    with patch(f"{MODULE}.async_unregister_panel", new=AsyncMock()):
        assert await async_unload_entry(hass, entry) is True

    controller.async_save_data.assert_awaited_once()
