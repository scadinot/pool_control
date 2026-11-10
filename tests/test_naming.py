"""Garde-fous de nommage après le renommage en ``pool_management``.

Ces tests ne vérifient pas un comportement mais une cohérence : qu'aucune
trace de l'ancien nom ne subsiste là où elle casserait quelque chose, et que
les identifiants dérivés les uns des autres restent d'accord entre eux.

Un renommage se trompe surtout dans ce que la suite n'exerce pas — une
constante qui nomme un fichier absent, une URL de panneau incohérente avec
le nom du Web Component. Ces échecs ne se manifestent qu'à l'exécution dans
Home Assistant, d'où ces assertions-ci.
"""

import json
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
COMPOSANT = RACINE / "custom_components" / "pool_management"

SUFFIXES_TEXTE = {".py", ".js", ".json", ".yaml", ".md"}


def _fichiers_texte(repertoire: Path):
    """Fichiers texte du répertoire, caches de bytecode exclus."""
    return [
        chemin
        for chemin in repertoire.rglob("*")
        if chemin.is_file()
        and chemin.suffix in SUFFIXES_TEXTE
        and "__pycache__" not in chemin.parts
    ]


def _manifeste() -> dict:
    return json.loads((COMPOSANT / "manifest.json").read_text(encoding="utf-8"))


@pytest.mark.unit
def test_le_domaine_et_le_dossier_concordent():
    """Home Assistant exige que le dossier porte le nom du domaine."""
    from custom_components.pool_management.const import DOMAIN

    assert DOMAIN == _manifeste()["domain"] == "pool_management"
    assert COMPOSANT.is_dir()


@pytest.mark.unit
def test_le_nom_affiche_est_coherent_entre_manifeste_et_hacs():
    manifeste = _manifeste()
    hacs = json.loads((RACINE / "hacs.json").read_text(encoding="utf-8"))

    assert manifeste["name"] == "Pool Management"
    assert hacs["name"] == manifeste["name"]


@pytest.mark.unit
def test_les_identifiants_derives_sont_coherents():
    """Ces constantes dérivent toutes du domaine et doivent rester d'accord.

    Une seule qui dérive produit une URL de panneau introuvable ou un Store
    écrit sous une clé que personne ne relit.
    """
    from custom_components.pool_management import controller, frontend

    assert controller.STORAGE_KEY == "pool_management_data"
    assert controller.STORAGE_KEY_PREFIX == "pool_management_data"
    assert frontend.STATIC_PATH == "/pool_management_static"
    assert frontend.PANEL_BASE_URL_PATH == "pool-management"
    assert frontend.PANEL_NAME == "pool-management-panel"
    assert frontend.DEFAULT_SLUG == "pool_management"
    assert frontend.PANEL_TITLE == "Pool Management"
    assert frontend.JS_FILENAME == "pool_management_panel.js"


@pytest.mark.unit
def test_le_fichier_du_panneau_existe_sur_disque():
    """Une constante qui nomme un fichier absent ne casse qu'au runtime.

    Aucun autre test ne touche le disque ici : sans cette assertion, une
    faute de frappe dans ``JS_FILENAME`` ne se verrait que dans Home
    Assistant, par un panneau vide.
    """
    from custom_components.pool_management import frontend

    assert (COMPOSANT / "frontend" / frontend.JS_FILENAME).is_file()


@pytest.mark.unit
def test_le_web_component_declare_le_nom_du_panneau():
    """``customElements.define`` doit employer exactement ``PANEL_NAME``."""
    from custom_components.pool_management import frontend

    js = (COMPOSANT / "frontend" / frontend.JS_FILENAME).read_text(encoding="utf-8")

    assert f"customElements.define('{frontend.PANEL_NAME}'" in js


@pytest.mark.unit
def test_aucune_trace_de_l_ancien_domaine_dans_le_composant():
    """Le composant ne doit plus nommer l'ancien domaine, nulle part.

    Le dépôt n'embarque aucune migration : rien n'a de raison légitime de
    nommer ``pool_control`` sous ``custom_components/``.
    """
    fautifs = []
    for chemin in _fichiers_texte(COMPOSANT) + [RACINE / "hacs.json"]:
        texte = chemin.read_text(encoding="utf-8")
        for motif in ("pool_control", "pool-control", "Pool Control"):
            if motif in texte:
                fautifs.append(f"{chemin.relative_to(RACINE)} : {motif}")

    assert fautifs == []


@pytest.mark.unit
def test_aucun_nom_de_classe_a_l_ancien_prefixe():
    """``PoolController`` reste : c'est du vocabulaire métier, pas la marque.

    Les autres classes portaient l'ancien nom de produit en préfixe. Le scan
    ci-dessus cherche « Pool Control » avec une espace et les laisserait
    passer, d'où ce test séparé.
    """
    fautifs = []
    for chemin in _fichiers_texte(COMPOSANT):
        texte = chemin.read_text(encoding="utf-8")
        for trouve in re.finditer(r"PoolControl(?!ler)", texte):
            ligne = texte[: trouve.start()].count("\n") + 1
            fautifs.append(f"{chemin.relative_to(RACINE)}:{ligne}")

    assert fautifs == []


@pytest.mark.unit
def test_le_readme_pointe_le_nouveau_depot():
    """Le scan ci-dessus ne couvre pas le README : les badges s'y vérifient ici.

    Le README nomme encore ``pool_control:`` une fois, à bon droit : c'est la
    section de ``configuration.yaml`` que les anciennes versions utilisaient
    et que l'utilisateur doit supprimer. La renommer inventerait un artefact
    qui n'a jamais existé.
    """
    readme = (RACINE / "README.md").read_text(encoding="utf-8")

    assert "scadinot/pool_control" not in readme
    assert "scadinot/pool_management" in readme
    assert readme.count("`pool_control:`") == 1


@pytest.mark.unit
def test_le_lint_de_la_ci_vise_le_bon_dossier():
    """Un lint braqué sur un dossier absent rapporte un succès sans rien lire."""
    workflow = (RACINE / ".github" / "workflows" / "tests.yaml").read_text(
        encoding="utf-8"
    )

    assert "custom_components/pool_management/" in workflow
    assert "custom_components/pool_control/" not in workflow
