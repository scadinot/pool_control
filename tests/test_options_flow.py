"""Tests de l'options flow, et notamment de ses champs optionnels d'entité.

Ces champs — traitement secondaire, pompe à chaleur et son capteur de
puissance — doivent pouvoir rester vides. Le piège est que ``vol.Optional``
assorti d'un ``default`` ne se contente pas de proposer une valeur : il
injecte la clé absente puis la valide. Un ``default`` à ``None`` fait donc
échouer le sélecteur d'entité sur ``Entity None is neither a valid entity
ID nor a valid UUID``, et le champ optionnel devient obligatoire.

Le pattern correct est ``description={"suggested_value": ...}``, qui
pré-remplit sans rien injecter.
"""

import pytest
import voluptuous as vol

from custom_components.pool_management.options_flow import (
    PoolManagementOptionsFlowHandler,
)

# Les sept entités que l'écran exige ou accepte hors PAC.
ENTITES_SANS_PAC = {
    "temperatureWater": "sensor.temperature_eau",
    "temperatureOutdoor": "sensor.temperature_air",
    "leverSoleil": "sensor.sun_next_rising",
    "filtration": "switch.filtration",
    "traitement": "switch.traitement_chlore",
    "traitement_2": "switch.traitement_ph",
    "surpresseur": "switch.surpresseur",
}


def _handler(options: dict) -> PoolManagementOptionsFlowHandler:
    """Construit un handler prêt à afficher un formulaire.

    ``flow_id`` et ``handler`` sont normalement posés par le gestionnaire
    de flow de Home Assistant ; on les fournit pour pouvoir appeler les
    étapes isolément.
    """

    handler = PoolManagementOptionsFlowHandler()
    handler.flow_id = "test-flow"
    handler.handler = "pool_management"
    handler.options = dict(options)
    return handler


async def _schema_de_l_ecran(options: dict) -> vol.Schema:
    """Retourne le schéma du formulaire des entités."""

    resultat = await _handler(options).async_step_user()
    return resultat["data_schema"]


@pytest.mark.bugs
async def test_sans_pac_le_formulaire_est_validable():
    """Sans pompe à chaleur, l'écran doit pouvoir être validé.

    Régression : ``heatPump`` déclaré avec ``default=None`` rendait le
    champ impossible à laisser vide, bloquant tout utilisateur sans PAC.
    """

    schema = await _schema_de_l_ecran(ENTITES_SANS_PAC)

    valide = schema(dict(ENTITES_SANS_PAC))

    assert "heatPump" not in valide
    assert "heatPumpPower" not in valide


@pytest.mark.bugs
async def test_sans_second_traitement_le_formulaire_est_validable():
    """Même piège sur ``traitement_2`` pour une installation à un seul relais."""

    entites = {
        cle: valeur
        for cle, valeur in ENTITES_SANS_PAC.items()
        if cle != "traitement_2"
    }

    schema = await _schema_de_l_ecran(entites)

    valide = schema(dict(entites))

    assert "traitement_2" not in valide


async def test_les_valeurs_existantes_sont_proposees():
    """Un champ optionnel déjà renseigné est pré-rempli, sans être imposé."""

    options = {**ENTITES_SANS_PAC, "heatPump": "switch.pac"}

    schema = await _schema_de_l_ecran(options)

    suggestions = {
        cle.schema: cle.description["suggested_value"]
        for cle in schema.schema
        if getattr(cle, "description", None)
    }
    assert suggestions["heatPump"] == "switch.pac"
    assert suggestions["traitement_2"] == "switch.traitement_ph"


async def test_les_champs_requis_le_restent():
    """Le correctif ne doit pas rendre facultatif ce qui ne l'est pas.

    On inspecte les marqueurs plutôt que de soumettre un formulaire
    incomplet : les champs requis portent un ``default``, que voluptuous
    injecte quand la clé manque. Une validation ne lèverait donc pas, et
    le test passerait quel que soit le marqueur.
    """

    schema = await _schema_de_l_ecran(ENTITES_SANS_PAC)
    marqueurs = {cle.schema: type(cle) for cle in schema.schema}

    for champ in (
        "temperatureWater",
        "temperatureOutdoor",
        "leverSoleil",
        "filtration",
        "traitement",
        "surpresseur",
    ):
        assert marqueurs[champ] is vol.Required, champ

    for champ in ("traitement_2", "heatPump", "heatPumpPower"):
        assert marqueurs[champ] is vol.Optional, champ


async def test_vider_un_champ_optionnel_l_efface():
    """Un champ vidé disparaît des options.

    Un champ laissé vide est absent des données soumises ; ``update`` ne
    supprimant rien, la valeur précédente survivrait sans retrait
    explicite — et le champ serait impossible à effacer une fois rempli.
    """

    handler = _handler({**ENTITES_SANS_PAC, "heatPump": "switch.pac"})

    await handler.async_step_user(dict(ENTITES_SANS_PAC))

    assert "heatPump" not in handler.options


async def test_un_champ_optionnel_renseigne_est_conserve():
    """À l'inverse, une valeur soumise est bien enregistrée."""

    handler = _handler(ENTITES_SANS_PAC)

    await handler.async_step_user(
        {**ENTITES_SANS_PAC, "heatPump": "climate.pac"}
    )

    assert handler.options["heatPump"] == "climate.pac"


async def test_les_autres_options_sont_preservees():
    """Soumettre l'écran des entités ne touche pas aux réglages des menus."""

    handler = _handler({**ENTITES_SANS_PAC, "sondeLocalTechnique": True})

    await handler.async_step_user(dict(ENTITES_SANS_PAC))

    assert handler.options["sondeLocalTechnique"] is True
