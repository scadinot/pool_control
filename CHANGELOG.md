# Changelog

Toutes les évolutions notables de Pool Control sont consignées dans ce fichier.

Le format est inspiré de [Keep a Changelog 1.1.0](https://keepachangelog.com/fr/1.1.0/) et le projet suit [Semantic Versioning](https://semver.org/lang/fr/).

## [Non publié]

## [0.0.19] — 2026-04-30

### Ajouté
- Support **multi-instance** : plusieurs piscines peuvent désormais cohabiter dans une même installation Home Assistant. Chaque instance dispose de son propre nom, ses propres entités et son propre stockage persistant.
- Champ **« Nom de l'instance »** dans le flux de configuration initiale, utilisé comme `unique_id` (via `slugify`) et comme titre de l'entrée.
- Validation côté UI : un nom vide ou non slugifiable est refusé (`error.invalid_name`) ; un nom déjà pris déclenche `abort.already_configured`.
- **Regroupement des entités sous un device** : les 15 entités d'une instance (6 capteurs + 9 boutons) apparaissent maintenant sous un même appareil typé `service` dans Home Assistant. L'intégration affiche « Services · Ajouter un service » au lieu de « Éléments de l'intégration ».
- Migration automatique **v1 → v2** des installations existantes :
  - reprise du titre comme nom d'instance et calcul de l'`unique_id`,
  - copie du store global `pool_control_data` vers la clé par instance `pool_control_data_<entry_id>`, puis suppression de l'ancienne clé,
  - **préfixage des `unique_id` du registre d'entités** par `entry_id` pour préserver les customisations utilisateur (icônes, area, nom personnalisé, désactivation) sans orpheliner les entités historiques.

### Modifié
- `manifest.json` : `version` `0.0.18` → `0.0.19`.
- `config_flow.py` : `VERSION = 2`, `async_set_unique_id` + `_abort_if_unique_id_configured` alignés sur le pattern de `shutters_management`.
- `__init__.py` : controllers stockés par `entry_id` (`hass.data[DOMAIN][entry_id]`) au lieu d'un singleton, déchargement multi-instance correctement scopé, ajout de `async_migrate_entry`.
- `entities.py` : déclaration d'un `DeviceInfo` (`entry_type=DeviceEntryType.SERVICE`, `manufacturer="Pool Control"`), `_attr_has_entity_name = True`, `unique_id` préfixé par `entry_id`.
- `controller.py` : accepte un `ConfigEntry` optionnel et dérive sa clé de `Store` de `entry_id` (l'ancienne clé est conservée comme fallback pour les usages hors-flow).
- `sensor.py`, `button.py` : récupèrent le controller scopé à `entry_id` et propagent `entry` aux entités.
- Traductions FR/EN + `strings.json` : champ `name`, `abort.already_configured`, `error.invalid_name`.

### Pas de breaking change
- La migration v1 → v2 est **automatique et silencieuse** au premier démarrage après l'upgrade. Aucune action utilisateur n'est requise, les entités existantes conservent leurs `entity_id` et leurs customisations.
- Les 350 tests passent sans modification du code de test.

### Note de migration
- Le minimum Home Assistant requis (`2026.3.0`) est inchangé.
- Après upgrade, l'intégration apparaît dans Paramètres → Appareils et services sous la forme « Pool Control · Ajouter un service », chaque pool figurant comme un appareil regroupant ses 15 entités.
- L'ajout d'une seconde piscine se fait via « Ajouter un service » et exige un nom distinct du premier.

## [0.0.18] — 2026-04-29

### Corrigé
- Crash `500 Internal Server Error` à la deuxième ouverture du flux d'options de l'intégration. Le constructeur de `PoolControlOptionsFlowHandler` n'assigne plus `self.config_entry` (devenu propriété en lecture seule depuis Home Assistant 2024.12) et s'aligne sur la signature moderne sans paramètre. `self.options` est désormais initialisé à la volée dans `async_step_init`.
- Suppression d'un `async_get_options_flow` mort au niveau module dans `__init__.py` (HA n'utilise que celui défini dans la classe `PoolControlConfigFlow`).

### Modifié
- `manifest.json` : `version` `0.0.17` → `0.0.18`.

## [0.0.17] — 2026-04-29

### Ajouté
- `ROADMAP.md` à la racine du dépôt, listant les évolutions à moyen et long terme ainsi que les pistes exploratoires.
- Nouvelle table des matières dans le `README.md`, alignée sur la convention du dépôt jumeau `shutters_management`.
- Section « Structure du dépôt » et bloc « Tests locaux » regroupés sous la rubrique « Contribuer » du `README.md`.

### Modifié
- `manifest.json` : `version` `0.0.16` → `0.0.17`.
- `hacs.json` : `render_readme` passé à `true` afin que HACS affiche directement `README.md`.
- `README.md` : réécriture complète selon la table des matières de référence (Fonctionnalités, Prérequis, Installation, Configuration, Comportement, Entités exposées, Tableau de bord, Surpresseur, Lavage, Migration, Roadmap, Changelog, Contribuer, Licence).
- `CHANGELOG.md` : réécriture au format Keep a Changelog 1.1.0, sans tableaux de scoring ni sections marketing.

### Supprimé
- `ANALYSIS.md` : document interne d'analyse, hors périmètre d'un dépôt distribué.
- `info.md` : vitrine HACS rendue inutile par `render_readme: true`.

### Pas de breaking change
- Aucune modification du code Python, du schéma de configuration, des entités ou des services.
- Les 350 tests passent sans modification.

### Note de migration
- Le minimum Home Assistant requis (`2026.3.0`) est inchangé par rapport à la v0.0.16. Les utilisateurs sur une version antérieure doivent rester sur la v0.0.16 jusqu'à mise à jour de leur Home Assistant.

## [0.0.16] — 2025-11-08

### Ajouté
- Mixin `ServiceMixin` (`service.py`) avec `_safe_service_call()` : wrapper de `hass.services.async_call` avec gestion d'erreurs, logging contextuel et retour booléen pour le suivi des échecs.

### Modifié
- 8 appels de services désormais sécurisés via `_safe_service_call()` : `filtration.py` (`filtrationOn`, `filtrationStop`), `traitement.py` (`traitementOn`, `traitementStop`, `traitement_2_On`, `traitement_2_Stop`), `surpresseur.py` (`surpresseurOn`, `surpresseurStop`).
- `controller.py` : intégration de `ServiceMixin` à la chaîne d'héritage.
- Suppression de 3 imports `Optional` inutilisés.

### Corrigé
- URL de documentation dans `manifest.json`.
- Métriques v0.0.15 dans le précédent `CHANGELOG.md`.
- Identifiants d'entités dans l'ancien `info.md`.

## [0.0.15] — 2025-11-04

### Ajouté
- Type hints sur les 82 fonctions et méthodes du code source (couverture annotation 100 %).

### Modifié
- Annotations de retour (`-> None`, `-> bool`, `-> str`, etc.) et de paramètres (`Optional`, `Any`, `Callable`, `Tuple`).
- Code source : 2362 → 2382 lignes.

## [0.0.14] — 2025-11-03

### Ajouté
- Création automatique des entités exposées par l'intégration : 6 capteurs et 9 boutons.
- Guide de migration depuis la configuration `configuration.yaml` historique.

### Modifié
- **Breaking** : l'installation passe par Config Flow UI ; la configuration via `configuration.yaml` n'est plus prise en charge.
- `README.md` : ré-organisation autour de la procédure d'installation par interface.
- Exemple de tableau de bord mis à jour avec les nouveaux identifiants d'entités.

### Supprimé
- Obligation de créer manuellement `input_button`, `input_text` et `input_number`.
- Instructions de configuration via `configuration.yaml`.

### Corrigé
- 3 tests précédemment en échec passent désormais (350/350).
- Métriques de test dans la documentation.

## [0.0.13] — 2025-11-02

### Ajouté
- 320 nouveaux tests, répartis sur 6 fichiers : `test_filtration.py`, `test_lavage.py`, `test_traitement.py`, `test_surpresseur.py`, `test_scheduler.py`, `test_utils.py`.
- Fixtures pour l'ensemble des composants de contrôle de filtration.

### Modifié
- Couverture de tests passée de 15 % à environ 65 %.
- Total : 30 → 350 tests, 2 → 12 fichiers de tests, 226 → 5432 lignes de tests.

### Corrigé
- `test_cron_full_5minute_cycle` : logique du compteur.
- `test_formatting_pads_single_digits` : précision de l'arrondi.
- `test_coefficient_affects_all_methods` : tolérance de comparaison flottante.

## [0.0.12] — 2025-11-01

### Ajouté
- Suite de tests initiale (30 tests).
- Workflows GitHub Actions : `tests.yaml`, `Validate HACS.yaml`, `Validate Hassfest.yaml`.
- Infrastructure de test : `conftest.py` avec 9 fixtures, `const.py`, `tests/README.md`.
- Tests de non-régression couvrant 6 bugs critiques (17 tests) et tests d'environnement (12 tests).

## [0.0.11] — 2025-10-31

### Modifié
- Documentation : reflet de l'architecture refactorisée et des bénéfices du refactoring.

## [0.0.10] — 2025-10-30

### Ajouté
- Architecture modulaire en 11 mixins : `ActivationMixin`, `ButtonMixin`, `FiltrationMixin`, `HivernageMixin`, `LavageMixin`, `SaisonMixin`, `SchedulerMixin`, `SensorsMixin`, `SurpresseurMixin`, `TraitementMixin`, `UtilsMixin`.
- Config Flow et Options Flow.
- Traductions FR / EN.
- Premiers type hints (15 fonctions).

### Modifié
- **Breaking** : `activation.py` refactorisé : 1 fonction monolithique → 13 fonctions modulaires, complexité ramenée sous 5, suppression du `# noqa: C901`.
- Architecture passée de monolithique (~1800 lignes dans `__init__.py`) à modulaire.

### Corrigé
- Méthode `executePoolStop()` manquante : remplacée par `executeButtonStop()`.
- `KeyError` sur `temperatureMaxi` : valeur par défaut ajoutée (8 occurrences).
- Message de log « Second cron » corrigé en « First cron ».
- Type `methodeCalcul` incohérent : conversion `int()` forcée.
- Crash si `traitement` non configuré : ajout de vérifications `None` (8 emplacements).
- Entité `temperatureDisplay` optionnelle : helper `updateTemperatureDisplay()`.

## [0.0.9] — Référence historique

Première version publique :

- Architecture monolithique (~1800 lignes dans `__init__.py`).
- Configuration via `configuration.yaml`.
- Contrôle de la filtration, du mode hivernage, du surpresseur et de l'assistant de lavage du filtre à sable.

Limitations connues à cette version : complexité de code élevée, pas de couverture de tests, pas de type hints, 6 bugs critiques (corrigés en 0.0.10).
