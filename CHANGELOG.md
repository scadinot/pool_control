# Changelog

Toutes les évolutions notables de Pool Control sont consignées dans ce fichier.

Le format est inspiré de [Keep a Changelog 1.1.0](https://keepachangelog.com/fr/1.1.0/) et le projet suit [Semantic Versioning](https://semver.org/lang/fr/).

## [Non publié]

## [0.0.29] — 2026-09-13

### Corrigé
- **Plages horaires décalées quand le fuseau du système diffère de celui de Home Assistant** : les pivots (saison, hivernage à heure fixe ou au lever du soleil), l'affichage du planning et les créneaux « 5 min / 3 h » étaient calculés dans le fuseau du système d'exploitation (souvent UTC dans un conteneur sans variable `TZ`), alors que `getLeverSoleil()` renvoie depuis la 0.0.28 l'heure dans le fuseau de Home Assistant. Sur ces installations, la filtration était décalée de l'écart entre les deux fuseaux (1 à 2 h en France). Tout est désormais calculé dans le fuseau de Home Assistant ; aucun changement lorsque les deux fuseaux sont identiques.
- **Pivot du lendemain décalé d'une heure les jours de changement d'heure** : il était obtenu en ajoutant 24 h au pivot du jour ; il est désormais recalculé à la même heure locale le lendemain.

### Modifié
- `utils.py` : nouveaux helpers `localDatetime()`, `formatTimestamp()` et `pivotTimestamp()` basés sur `homeassistant.util.dt`.
- `saison.py`, `hivernage.py`, `buttons.py`, `scheduler.py` : plus aucun appel à `datetime.today()` / `datetime.now()` / `datetime.fromtimestamp()` dépendant du fuseau du système.
- Tests : fixture `ha_time_zone` (fuseau HA volontairement différent de celui de la machine de test) ; tests de lendemain et « 5 min / 3 h » réécrits avec des horodatages explicites ; nouveaux tests (fuseau HA, changement d'heure, bug #9).
- `manifest.json` : `version` `0.0.28` → `0.0.29`.

### Pas de breaking change
- Aucune action utilisateur requise, aucune entité ni option modifiée.
- Lorsque le fuseau du système est déjà celui de Home Assistant (cas de Home Assistant OS), seul le calcul du pivot du lendemain les jours de changement d'heure change.

## [0.0.28] — 2026-09-13

### Corrigé
- **Heure de lever du soleil décalée en hivernage** : `sensor.sun_next_rising` est exprimé en UTC et l'heure en était extraite telle quelle, décalant le pivot d'hivernage de 1 à 2 h en France (ex. 05:33 au lieu de 07:33). L'horodatage est désormais converti dans le fuseau de Home Assistant (`dt_util.as_local`). Un état non horodaté (`unavailable`, `unknown`) ne fait plus planter le cron : repli sur `06:00` avec un log d'erreur.
- **Surpresseur bloqué en marche après un redémarrage** : si Home Assistant redémarrait (ou si l'intégration était rechargée) pendant un cycle surpresseur ou lavage, le cron « 5 secondes » n'était pas relancé ; le compte à rebours n'était plus suivi et le surpresseur restait actif jusqu'à un appui sur Stop. Le cycle est désormais repris au démarrage (`resumeSecondCron`) : il se termine normalement, ou immédiatement si sa durée est écoulée. L'étape d'attente de l'assistant de lavage (« Arrêt, position … ») est réaffichée.

### Modifié
- `manifest.json` : `version` `0.0.27` → `0.0.28`.
- `sensors.py` : `getLeverSoleil()` utilise `dt_util.parse_datetime()` + `dt_util.as_local()`.
- `scheduler.py` : nouvelle méthode `resumeSecondCron()`, appelée par `async_setup_entry()` après la création des capteurs.
- `lavage.py` : messages d'attente regroupés dans `LAVAGE_ATTENTE_STATUS`.
- 15 nouveaux tests (non-régression bugs #7 et #8, `TestResumeSecondCron`) : 376 tests passent.

### Pas de breaking change
- Aucune action utilisateur requise, aucune entité ni option modifiée.
- En mode Saison, le comportement est inchangé. En mode Hivernage avec « Lever du soleil », la plage de filtration est recalée sur l'heure locale réelle au prochain calcul (ou via le bouton Reset).

## [0.0.27] — 2026-05-07

### Ajouté
- **Synoptique 8 étapes** dans le panneau, aligné sur un schéma 3D photoréaliste de référence :
  1. Aspiration via skimmer
  2. Aspiration via bonde de fond
  3. Pompe de filtration
  4. Filtre à sable (vanne 6 voies, manette latérale)
  5. **Pompe à chaleur via by-pass** (nouveau) — boîtier extérieur avec hélice frontale + 2 vannes 3 voies bleues qui matérialisent le by-pass
  6. Analyse et injection pH (sonde dans le tuyau + boîtier mural avec écran + bidon)
  7. Analyse et injection chlore (idem séparé du pH)
  8. Retour piscine
- **Champ optionnel `heatPump`** dans le config flow et l'options flow (sélecteur d'entité, domaines `switch`, `input_boolean`, `climate`). Permet de relier une PAC pilotée par une autre intégration HA pour visualiser son état dans le synoptique.
- **Animation contextuelle PAC** :
  - PAC non configurée → boîtier représenté en transparence (`.pac-housing` opacity 0.55), eau passe par le by-pass court-circuit (`.flow-bypass`).
  - PAC configurée mais OFF → boîtier opaque, eau toujours par le by-pass.
  - PAC configurée et ON → hélice tourne (`.pac-rotor`), particules d'eau passent par le chemin PAC (`.flow-pac`), le by-pass est éteint visuellement.
- **Frise pédagogique** en bas du SVG avec les 8 étapes représentées en cercles bleus numérotés et reliés par des flèches, sur fond blanc translucide.
- **Encart de légende** en haut-gauche avec la liste numérotée 1–8 des étapes (style identique à l'image de référence).
- **Badge « Sens de circulation de l'eau »** en bas à gauche.

### Modifié
- `manifest.json` : `version` `0.0.26` → `0.0.27`.
- `frontend/pool_control_panel.js` :
  - `viewBox` agrandi de `1200×720` à `1400×960` pour accueillir tous les éléments + frise + encart légende.
  - Ajout des hooks `_heatPumpEntity` (constructeur + setter `hass`), `_isHeatPumpRunning()`, et toggle des classes `.heat-pump-active` / `.heat-pump-configured` sur le SVG dans `_update()`.
  - Nouveaux keyframes CSS : `flowPac`, `flowBypass`, `.pac-rotor` (rotation lente 1.6s), `.pac-housing` (transition d'opacité). `prefers-reduced-motion` couvre les nouvelles animations.
  - Réécriture complète de `_svgMarkup()` : décor (mur béton, sol carrelé, néon plafond, coffret électrique mural, bassin en perspective cavalière, galets extérieurs), tuyauterie redessinée avec les 5 segments d'écoulement (`flow-asp`, `flow-pf`, `flow-fr`, `flow-bypass` ou `flow-pac` selon état, `flow-ret`), labels chips et numéros stylisés.
- `config_flow.py` et `options_flow.py` : nouveau `vol.Optional("heatPump")` dans le schéma user / step user, sans rupture pour les installations existantes (`vol.Optional` ne casse rien).
- `frontend.py` : transmet `heat_pump_entity` au Web Component via `panel.config`.
- Traductions FR/EN + `strings.json` : libellé « Pompe à chaleur (optionnel) » / « Heat pump (optional) » dans `config.step.user.data.heatPump` et `options.step.user.data.heatPump`.

### Pas de breaking change
- Les installations 0.0.26 sans PAC continuent à fonctionner sans aucune action utilisateur (`heatPump = None`).
- Aucune logique métier Pool Control n'est modifiée — la PAC n'est pas pilotée par l'intégration, elle est juste visualisée dans le panneau.
- 361 tests passent sans modification.

### Note de migration
- Pour ajouter une PAC à un setup existant : Paramètres → Pool Control → Configurer → Configuration des entités → renseigner « Pompe à chaleur (optionnel) » → Sauvegarder. Le panneau se recharge automatiquement et reflète l'état de l'entité choisie.

## [0.0.26] — 2026-05-07

### Modifié
- **Refonte du synoptique hydraulique** dans le panneau, inspirée d'un schéma 3D photoréaliste. Le SVG est repensé en perspective semi-isométrique sur fond sol/bassin, et passe de 4 à **6 éléments illustrés** :
  1. Skimmer + Bonde de fond (aspirations multiples côté bassin),
  2. Pompe avec préfiltre, moteur arrière et rotor qui tourne pendant la filtration,
  3. Filtre à sable beige avec vanne 6 voies (manette latérale),
  4. Traitement pH (boîtier bleu doseur + bidon « pH » étiqueté),
  5. Traitement chlore (boîtier jaune doseur + bidon « Chlore » étiqueté),
  6. Refoulement (buse de retour au bassin via tuyau qui longe le sol).
- **Tuyauterie PVC** retracée avec gradients gris foncé pour évoquer le PVC, raccordée précisément à chaque élément. Les flèches d'écoulement (water particles) suivent désormais 4 segments cohérents :
  - Aspiration : skimmer + bonde de fond → pompe
  - Refoulement pompe → filtre (entrée vanne 6 voies)
  - Filtre → doseurs pH puis chlore
  - Retour au bassin par le sol jusqu'à la buse de refoulement
- **Légende numérotée** (1–6) intégrée dans le SVG en bas à gauche, sur fond `#0b1620` translucide, accompagnée de pastilles ambrées sur chaque élément du schéma.
- **Labels chips** (« Skimmer », « Bonde de fond », « Pompe », « Filtre à sable », « Traitement pH », « Traitement chlore ») en pill `rgba` sombre placés directement sur le SVG.
- `viewBox` du SVG passé de `0 0 1100 560` à `0 0 1200 720` pour accueillir tous les éléments avec respiration.
- `transform-origin` du `.pump-rotor` ajusté à la nouvelle position du rotor (`600px 540px`).

### Pas de breaking change
- Aucun changement Python : `frontend.py`, `__init__.py`, `manifest.json` (hors version), tests et logique métier sont strictement identiques.
- Aucun changement de la logique JS du Web Component : `set hass`, `_update`, `_isFiltrationRunning`, `_controlMode`, `_backwashStep`, `_callService`, `_pressButton` sont inchangés. Les hooks d'animation (`.running`, `.stopped`, `.backwash-active`, `.pump-rotor`, `.flow-asp/pf/fr/ret`, `#status-led-text`, `.filtre-rect`) sont préservés.
- 361 tests passent sans modification.

### Note de migration
- Aucune action utilisateur requise. Le nouveau synoptique apparaît automatiquement après upgrade HACS et redémarrage HA.

## [0.0.25] — 2026-05-07

### Modifié
- **Refonte UI complète du panneau latéral** : passage à un style dashboard moderne avec glassmorphism, hiérarchie typographique soignée, transitions fluides et mise en page restructurée.
  - Cards en glassmorphism (`backdrop-filter: blur(24px) saturate(180%)`, ombres profondes, bordure haute éclairée pour effet de profondeur).
  - Background du panneau en gradient radial deux passes (cyan eau + amber air) sur fond deep navy, qui se replie sur la variable HA `--primary-background-color` en thème clair.
  - Hiérarchie typo : températures en chiffres `44px weight 200`, statut principal en `22px weight 300`, titres de sections en `11px UPPERCASE letter-spacing 0.18em`. Échelle d'espacements 4px (`8/12/16/24/32`).
  - Layout desktop corrigé via une **grille 12 colonnes** : Hero (8) + Modes (4) en haut, puis Schéma (8) + stack Surpresseur/Lavage (4). Ne laisse plus de zone vide à droite comme la 0.0.23.
  - **Toggle groups** « pill connectée » pour Activation (Actif/Auto/Inactif) et Saison (Saison/Hivernage), avec glow contextuel sur le bouton actif (cyan / amber / bleu).
  - Transitions Material `cubic-bezier(0.4, 0, 0.2, 1)` à 160 / 220 / 320 ms. Animation d'entrée cascadée sur les cards à chaque premier render.
  - Bandeau d'instruction de vanne (glassmorphism amber, pulsation douce par `box-shadow`) avec icône 👉 désormais en pseudo-élément `::before` séparé du texte.
  - Header sticky avec backdrop-filter, sous-titre « TABLEAU DE BORD », et badge de statut en pill arrondie avec glow contextuel selon l'état (vert / bleu / gris / neutre).

### Pas de breaking change
- Aucun changement Python : `frontend.py`, `__init__.py`, `manifest.json` (hors version), tests, traductions et logique métier sont strictement identiques.
- Aucun changement de la logique JS du Web Component : `set hass`, `_update`, `_isFiltrationRunning`, `_controlMode`, `_backwashStep`, `_callService`, `_pressButton` et l'ensemble du SVG hydraulique sont inchangés. Tous les `entity_id` ciblés et tous les IDs DOM internes du panneau sont préservés.
- 361 tests passent sans modification.

### Note de migration
- Aucune action utilisateur requise : le nouveau panneau est servi automatiquement après upgrade HACS et redémarrage HA. La sidebar et l'URL `/pool-control[-<slug>]` ne changent pas.

## [0.0.24] — 2026-05-07

### Corrigé
- **Panneau latéral compatible multi-instance.** La 0.0.23 enregistrait toujours le panneau sur l'URL fixe `/pool-control` et avec le titre figé « Pool Control ». Avec plusieurs ConfigEntry, la première gagnait, les suivantes étaient ignorées, et décharger une instance retirait le panneau pour toutes les autres. La 0.0.24 calcule désormais l'URL et le titre par instance :
  - l'instance par défaut (slug `pool_control`) garde l'URL historique `/pool-control` et le titre « Pool Control » (pas de rupture pour les bookmarks),
  - chaque instance supplémentaire reçoit `/pool-control-<slug>` (ex. `/pool-control-piscine`, `/pool-control-spa`) et le titre « Pool Control · <nom> ».

  `async_unregister_panel` ne touche plus qu'au panneau de l'instance déchargée.

- **Appel `hass.callService` côté JS conforme à la signature standard.** Le 4ᵉ paramètre `target` était passé en plus du `serviceData` ; certaines versions du frontend HA l'ignoraient et déclenchaient le service sans `entity_id`, rendant les boutons inopérants. Le `entity_id` est désormais inclus directement dans le `serviceData` (3 paramètres seulement).

### Modifié
- `manifest.json` : `version` `0.0.23` → `0.0.24`.
- `frontend.py` : nouvelles helpers `_panel_url_path(slug)` et `_sidebar_title(slug, entry_title)`. `async_register_panel(hass, slug, entry_title, config_entry_data)` et `async_unregister_panel(hass, slug)` prennent désormais le slug d'instance en argument.
- `__init__.py` : nouvelle helper `_slug_from_entry(entry)` qui calcule le slug depuis `entry.unique_id` (avec fallback `slugify(entry.title)`). Appliquée dans `async_setup_entry`, `async_unload_entry` et `_async_update_panel`.
- `frontend/pool_control_panel.js` : `_callService` utilise `(domain, service, { entity_id: target })` au lieu de l'ancienne forme à 4 arguments.
- `tests/test_frontend.py` : 5 tests adaptés à la nouvelle signature, dont un test de non-régression vérifiant qu'une 2ᵉ instance reçoit une URL et un titre distincts, et qu'`async_unregister_panel` ne touche pas aux autres instances. Réutilise désormais la fixture commune `mock_hass` (étendue avec les attributs `http` requis) au lieu de redéfinir une fixture `hass` ambiguë.

### Note de migration
- Pour les instances existantes 0.0.23 dont le slug n'est pas `pool_control` (ex. instance « Piscine » → slug `piscine`), l'URL passe de `/pool-control` à `/pool-control-piscine` après upgrade. Les bookmarks utilisateurs sur l'ancienne URL doivent être mis à jour. La sidebar HA se met à jour automatiquement.

## [0.0.23] — 2026-04-30

### Ajouté
- **Panneau latéral Home Assistant** dédié à Pool Control. Une entrée apparaît dans la sidebar (à côté de « Vue d'ensemble », « Énergie », …) et ouvre une vue full-page comprenant un schéma hydraulique animé (SVG vanilla, animation pilotée par classes CSS), des tuiles températures eau / air, l'état complet du contrôleur (statut, planning, temps calculé), les boutons de mode (Actif / Auto / Inactif) et de saison (Saison / Hivernage), les commandes du surpresseur et l'automate de lavage du filtre avec **instructions visuelles pour positionner la vanne 6 voies**. Le panneau s'adapte automatiquement au thème HA actif et se recharge tout seul quand les options de l'intégration changent.

### Modifié
- `manifest.json` : `version` `0.0.22` → `0.0.23`. Ajoute `frontend`, `http` et `panel_custom` aux dépendances HA.
- `__init__.py` : `async_setup_entry` enregistre le panneau via `frontend.py` après les plateformes, et branche un update listener pour le recharger quand les options changent. `async_unload_entry` retire le panneau avant tout autre cleanup. Nouvelle helper `_build_panel_config(entry)` qui calcule l'`instance_prefix` à partir de `entry.unique_id` (avec fallback `slugify(entry.title)`).

### Nouveau
- `custom_components/pool_control/frontend.py` : enregistrement du Web Component et du chemin statique (`/pool_control_static/`) servant `pool_control_panel.js`. API conforme HA 2026.3 (`StaticPathConfig`, `async_register_static_paths`, `panel_custom.async_register_panel`).
- `custom_components/pool_control/frontend/pool_control_panel.js` : Web Component vanilla JS (~32 ko), pas de build, pas de dépendances externes. Lit les états via `hass.states`, écrit via `hass.callService()`. Le SVG du schéma est statique, animation pilotée par les classes `.running` / `.stopped` / `.backwash-active` mises à jour à chaque setter `hass`.
- `tests/test_frontend.py` : 4 tests de non-régression sur l'enregistrement et le retrait idempotents du panneau.

### Pas de breaking change
- Le panneau est complémentaire au dashboard Lovelace : les deux coexistent sans interférer.
- 360 tests (356 + 4 nouveaux) passent sans modification du code de test existant.

## [0.0.22] — 2026-04-30

### Corrigé
- **L'`entity_id` est désormais réellement stable et indépendant de la langue active.** Le fix de la 0.0.21 utilisait `_attr_suggested_object_id`, propriété qui **n'existe pas** dans Home Assistant : `helpers/entity.py` ne lit que la *property* `suggested_object_id` (et celle-ci retourne le nom traduit). Conséquence : la suggestion était purement et simplement ignorée, et l'`entity_id` continuait d'être dérivé du nom traduit (`button.pool_control_actif` quand HA était en français au moment de la création).

  La 0.0.22 abandonne cette propriété fantôme et définit directement `self.entity_id` dans `__init__` — c'est le contrat documenté par `entity_platform.py:823-845` (« An entity may suggest the entity_id by setting entity_id itself »). Cette fois, l'identifiant est vraiment figé en anglais quelle que soit la langue HA.

### Modifié
- `manifest.json` : `version` `0.0.21` → `0.0.22`.
- `entities.py` : `_build_suggested_object_id(entry, translation_key)` remplacée par `_build_entity_id(platform, entry, translation_key)` qui retourne directement `f"{platform}.{prefix}_{translation_key}"`. `PoolControlStatusSensor` et `PoolControlButton` posent désormais `self.entity_id` au constructeur (au lieu du `_attr_suggested_object_id` ignoré).
- `tests/test_entities.py` : adapté à la nouvelle helper, +1 test (`test_platform_prefix_is_respected`).

### Note de migration
- Les entités créées sous la 0.0.21 (avec ou sans le fix censé être appliqué) conservent leur `entity_id` historique tant que leur `unique_id` est inchangé.
- Pour bénéficier des nouveaux IDs anglais (`button.<instance>_active`, …) sur une installation existante : supprimer puis recréer l'instance **après** avoir mis à jour vers la 0.0.22 et redémarré HA.

## [0.0.21] — 2026-04-30

### Corrigé
- `entity_id` désormais réellement stables et indépendants de la langue active. La 0.0.20 posait bien `_attr_translation_key`, mais Home Assistant dérivait l'`object_id_base` du nom traduit dans la langue active **au moment de la création** de l'entité, produisant par exemple `button.pool_control_actif` au lieu de `button.pool_control_active` quand l'instance était créée avec HA en français. L'ajout de `_attr_suggested_object_id = "<slug(entry.title)>_<translation_key>"` force un identifiant anglais quelle que soit la langue HA.

### Modifié
- `manifest.json` : `version` `0.0.20` → `0.0.21`.
- `entities.py` : nouvelle helper `_build_suggested_object_id(entry, translation_key)` ; `PoolControlStatusSensor` et `PoolControlButton` posent désormais `_attr_suggested_object_id`.

### Note de migration
- Les entités créées sous la 0.0.20 conservent leur `entity_id` historique (`button.<instance>_actif`, …) tant que leur `unique_id` est inchangé. Pour bénéficier des nouveaux IDs anglais (`button.<instance>_active`, …) sur une installation existante :
  - soit renommer manuellement chaque entité dans Paramètres → Appareils et services → ouvrir l'entité → champ `entity_id`,
  - soit supprimer puis recréer l'instance **après** un redémarrage de HA (en acceptant la perte de configuration et de l'état persistant).

## [0.0.20] — 2026-04-30

### Ajouté
- **`entity_id` internationaux et stables** via `_attr_translation_key`. Les nouvelles installations exposent des identifiants en anglais (`sensor.<instance>_filtration_time`, `button.<instance>_reset`, …) indépendants de la langue de l'interface.
- **Libellés affichés localisés** dans le frontend Home Assistant : noms d'entités en français ou en anglais selon la langue de l'utilisateur, sans modifier l'`entity_id`. Les libellés sont définis dans `entity.sensor.*.name` et `entity.button.*.name` des fichiers `translations/fr.json` et `translations/en.json`.

### Modifié
- `manifest.json` : `version` `0.0.19` → `0.0.20`.
- `entities.py` : `PoolControlStatusSensor` et `PoolControlButton` reçoivent désormais une `translation_key` (anglaise stable) à la place d'un `name` français. `_attr_translation_key` remplace `_attr_name`.
- `sensor.py`, `button.py` : passage des `translation_key` au lieu des noms français.
- `translations/fr.json`, `translations/en.json`, `strings.json` :
  - ajout de la section `entity.sensor.*` avec 6 clés (`control_status`, `filtration_time`, `filtration_schedule`, `filtration_status`, `booster_status`, `backwash_status`),
  - renommage des clés `entity.button.*` vers leurs équivalents anglais stables (`active`, `inactive`, `winter`, `season`, `booster`, `backwash`).
- `README.md` :
  - section « Entités exposées » mise à jour avec les nouveaux `entity_id` stables et un avertissement sur le préfixe d'instance,
  - section « Tableau de bord » réécrite avec les `entity_id` anglais cohérents.

### Pas de breaking change
- Les installations existantes conservent leurs `entity_id` historiques (`sensor.temps_de_filtration`, `button.actif`, …) tels qu'inscrits dans le `entity registry` de Home Assistant. Les `unique_id` restent identiques, donc HA n'efface ni ne renomme aucun `entity_id`. Les automatisations basées sur les anciens IDs continuent de fonctionner sans modification.
- Les 350 tests passent sans modification du code de test.

### Note de migration
- Pour aligner manuellement une installation existante sur les nouveaux `entity_id` : Paramètres → Appareils et services → Pool Control → ouvrir chaque entité → renommer l'`entity_id`. La suppression puis recréation de l'instance n'est **pas** recommandée pour cet usage car elle efface également la configuration (entités source, options avancées) et l'état persistant ; il faudrait reconfigurer l'intégration de zéro.
- L'ajout d'une **nouvelle** instance après upgrade hérite directement des `entity_id` anglais stables.

## [0.0.19] — 2026-04-30

### Ajouté
- Support **multi-instance** : plusieurs piscines peuvent désormais cohabiter dans une même installation Home Assistant. Chaque instance dispose de son propre nom, ses propres entités et son propre stockage persistant.
- Champ **« Nom de l'instance »** dans le flux de configuration initiale, utilisé comme `unique_id` (via `slugify`) et comme titre de l'entrée.
- Validation côté UI : un nom vide ou non slugifiable est refusé (`error.invalid_name`) ; un nom déjà pris déclenche `abort.already_configured`.
- **Regroupement des entités sous un device** : les 15 entités d'une instance (6 capteurs + 9 boutons) apparaissent maintenant sous un même appareil typé `service` dans Home Assistant. L'intégration affiche « Pool Control · Ajouter un service » au lieu de « Pool Control · Ajouter une entrée ».
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
