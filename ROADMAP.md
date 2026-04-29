# Feuille de route — Pool Control

Ce document liste les évolutions envisagées pour Pool Control. Il est volontairement plus large que le `CHANGELOG.md` (qui consigne ce qui a été livré) et a vocation à être discuté via les issues GitHub avant tout démarrage d'implémentation.

## Vue d'ensemble

| Horizon | Objectif | Effort estimé |
|---------|----------|---------------|
| Court terme | Stabiliser la documentation et l'expérience HACS | Faible |
| Moyen terme | Atteindre la **v0.1.0** : multi-instance, templates Jinja, profil saisonnier, notifications | Moyen |
| Long terme | Atteindre la **v1.0.0** : statistiques, calendrier de maintenance, tableau de bord packagé, API publique stable | Élevé |
| Exploratoire | Domotique avancée : pH/Redox, pompe à vitesse variable, volet, détection de fuite | Variable |

## Statut actuel

La version courante est **0.0.17** : refonte documentaire, alignement de la présentation sur le dépôt jumeau `shutters_management` et bascule de HACS sur `render_readme`. Aucun changement fonctionnel par rapport à 0.0.16. Pour le détail des évolutions livrées, voir [CHANGELOG.md](CHANGELOG.md).

## Moyen terme — fonctionnalités v0.1.0

### 1. Support multi-instance

Permettre la déclaration de plusieurs piscines ou spas distincts sous le même domaine `pool_control`.

- **Motivation** : couvrir les utilisateurs disposant de plusieurs bassins (piscine principale + spa, par exemple), sans avoir à dupliquer l'intégration ou contourner via plusieurs comptes Home Assistant.
- **Piste technique** :
  - Rendre `CONF_NAME` requis et unique dans le Config Flow.
  - Scoper tous les signaux internes par `entry_id` plutôt que par domaine.
  - Préfixer les `entity_id` générés par le slug du nom (`sensor.<slug>_filtration_status`).
  - Ajouter une migration douce pour les configurations existantes qui n'ont qu'une instance.

### 2. Templates Jinja dans les heures pivots

Autoriser des expressions Jinja là où une heure fixe est attendue aujourd'hui.

- **Motivation** : permettre par exemple `{{ states('input_datetime.pool_pivot') }}` ou un calcul dynamique fonction du fuseau, du tarif d'électricité ou d'un planning extérieur.
- **Piste technique** :
  - Côté schéma : remplacer `cv.string` par `cv.template` pour `datePivot` et `datePivotHivernage` dans `options_flow.py`.
  - Côté runtime : appeler `Template.async_render()` à chaque cycle de calcul dans `saison.py` et `hivernage.py`, avec un fallback explicite si le template échoue.
  - Documenter les variables exposées au template (heure courante, lever/coucher du soleil, températures).

### 3. Profil saisonnier

Coefficients d'ajustement distincts pour printemps / été / automne, sélectionnables manuellement ou automatiquement.

- **Motivation** : la même piscine consomme et se contamine différemment selon la saison ; un coefficient unique force des compromis.
- **Piste technique** :
  - Nouvelle clé `seasonProfile` dans l'`OptionsFlow`, sous forme de table de coefficients indexée par mois.
  - Résolution du coefficient courant au début de chaque cycle dans `utils.py::calculateTimeFiltrationWithCurve`.
  - Sélecteur Lovelace `select.pool_control_season_profile` pour forcer manuellement un profil (utile en demi-saison).

### 4. Notifications optionnelles

Émettre des notifications Home Assistant aux moments clés.

- **Motivation** : l'utilisateur ne sait pas aujourd'hui que la marche forcée hors-gel a été déclenchée, ni qu'un cycle de lavage a été interrompu.
- **Piste technique** :
  - Champ optionnel `notifyService` dans l'Options Flow (par défaut vide).
  - Helper centralisé dans `service.py` qui appelle `notify.<service>` avec un message localisé via `strings.json`.
  - Événements couverts : démarrage / arrêt de la filtration, transitions saison ↔ hivernage, déclenchement / fin du hors-gel, étape de l'assistant de lavage.

## Long terme — stabilisation v1.0.0

### 5. Statistiques de filtration

Capteurs cumulatifs : `sensor.pool_control_total_filtration_minutes_today`, `_this_week`, `_this_month`, `_year_to_date`.

- **Motivation** : permettre à l'utilisateur de vérifier que le temps de filtration réel correspond bien au temps calculé, et d'alimenter ses propres tableaux de bord énergie.
- **Piste technique** :
  - Utiliser `RestoreEntity` pour persister les compteurs au redémarrage.
  - Cumul incrémental dans la boucle `cron()` du `SchedulerMixin`.
  - Exposition au format `device_class: duration` pour intégration native avec les dashboards énergie.

### 6. Tableau de bord Lovelace dédié

Carte `custom-element` packagée séparément (`pool_control-card`).

- **Motivation** : l'exemple YAML du README est long et peu accessible aux utilisateurs débutants. Une carte unique offre une expérience « plug and play ».
- **Piste technique** :
  - Repo séparé suivant les conventions HACS pour les cartes Lovelace.
  - Réplique du layout YAML actuel en widget unique avec props pour personnalisation (couleurs, masquer certains boutons).

### 7. Calendrier de maintenance

Entité `calendar.pool_control_maintenance` listant les rappels d'entretien.

- **Motivation** : l'entretien d'une piscine suit un calendrier à plusieurs strates (lavage filtre, traitement choc, hivernage à date) facile à oublier.
- **Piste technique** :
  - Heuristique de rappel lavage filtre : nombre d'heures cumulées de filtration depuis le dernier lavage (réinitialisé à la fin de l'assistant).
  - Rappel traitement choc : périodicité configurable.
  - Rappel hivernage / mise en route : à date fixe ou via seuil de température.

### 8. Stabilisation de l'API publique

Figer noms d'entités, services et structure des données pour passer en `1.0.0`.

- **Motivation** : aujourd'hui, chaque mineure peut renommer un capteur. Au-delà de `1.0.0`, on s'engage à ne breaker que sur bump majeur.
- **Piste technique** :
  - Audit exhaustif des `entity_id` et des clés de services exposés.
  - Implémentation de `async_migrate_entry` pour absorber les renommages sans casser les configurations utilisateurs.
  - Documentation explicite de la matrice de compatibilité dans `README.md`.

## Pistes exploratoires

Items dont l'utilité a été identifiée mais qui n'ont pas encore de piste d'implémentation détaillée. Ils sont listés ici pour invitation à discussion :

- **Capteurs pH / Redox + dosage automatique** : intégrer un capteur pH et déclencher un dosage chlore / pH minus / pH plus en fonction. Demande un travail conséquent sur la sécurité (verrouillage hardware, limites max de dosage).
- **Pompe à vitesse variable (VFD)** : remplacer le pilotage on/off par une cible de débit ou de vitesse. Implique de revoir le calcul de filtration en termes d'énergie plutôt qu'en heures.
- **Couverture / volet automatique** : fermer le volet en fin de cycle, ouvrir avant. Nécessite un nouvel actionneur dans le Config Flow et une intégration optionnelle.
- **Détection de fuite** : analyse statistique des cycles d'appoint d'eau si un capteur de niveau est présent. Alerte si la fréquence d'appoint dépasse un seuil.

## Contribuer à cette feuille de route

Les propositions sont les bienvenues — ouvrir une issue avant une PR pour valider la direction :

- Ouvrez une issue décrivant le besoin métier avant la PR.
- Respectez les conventions de commit du dépôt (impératif court, scope explicite).
- Vérifiez localement que `pytest tests/` reste vert avant de pousser.
- Pour toute fonctionnalité visible côté utilisateur, ajoutez une entrée correspondante dans `CHANGELOG.md` sous `## [Non publié]`.
