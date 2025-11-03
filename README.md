# Pool Control

[![Tests](https://github.com/scadinot/pool_control/actions/workflows/tests.yaml/badge.svg)](https://github.com/scadinot/pool_control/actions/workflows/tests.yaml)
[![HACS](https://github.com/scadinot/pool_control/actions/workflows/Validate%20HACS.yaml/badge.svg)](https://github.com/scadinot/pool_control/actions/workflows/Validate%20HACS.yaml)
[![Hassfest](https://github.com/scadinot/pool_control/actions/workflows/Validate%20Hassfest.yaml/badge.svg)](https://github.com/scadinot/pool_control/actions/workflows/Validate%20Hassfest.yaml)

_Composant Home Assistant permettant de gérer la filtration d'une piscine en fonction de la température._

## Fonctionnalités

- Hivernage actif.
- Filtre à sable.
- Surpresseur pour robot nettoyeur.
- Configuration via l'interface utilisateur (Config Flow).
- Création automatique des capteurs et boutons.

## Installation

### Installation HACS (Recommandé)

1. Installez [HACS](https://hacs.xyz/). Vous recevrez ainsi les mises à jour automatiquement.
2. Ajoutez ce dépôt Github comme dépôt personnalisé dans les paramètres de HACS.
3. Recherchez et installez "Pool Control" dans HACS et cliquez sur `TÉLÉCHARGER`.
4. Redémarrez Home Assistant.
5. Allez dans **Paramètres** → **Appareils et services** → **Ajouter une intégration** et recherchez "Pool Control".

### Installation manuelle

1. En utilisant l'outil de votre choix, ouvrez le répertoire (dossier) de votre configuration HA (où vous trouverez `configuration.yaml`).
2. Si vous n'avez pas de répertoire (dossier) `custom_components`, vous devez le créer.
3. Dans le répertoire (dossier) `custom_components`, créez un nouveau dossier appelé `pool_control`.
4. Téléchargez _tous_ les fichiers du répertoire (dossier) `custom_components/pool_control/` de ce dépôt Github.
5. Placez les fichiers que vous avez téléchargés dans le nouveau répertoire (dossier) que vous avez créé.
6. Redémarrez Home Assistant.
7. Allez dans **Paramètres** → **Appareils et services** → **Ajouter une intégration** et recherchez "Pool Control".

## Configuration

### Configuration initiale via l'interface utilisateur

Lors de l'ajout de l'intégration via **Paramètres** → **Appareils et services** → **Ajouter une intégration**, vous devrez fournir les informations suivantes :

#### Capteurs requis

- **Température de l'eau** : Sélectionnez le capteur de température de votre piscine (sensor ou input_number)
- **Température extérieure** : Sélectionnez le capteur de température de l'air (sensor ou input_number)
  - Si vous ne disposez pas d'une sonde de température extérieure, vous pouvez utiliser une donnée météo
- **Lever du soleil** : Sélectionnez le capteur indiquant l'heure de lever du soleil (généralement `sensor.sun_next_rising`)

#### Actionneurs requis

- **Filtration** : Sélectionnez le relais contrôlant la pompe de filtration (switch ou input_boolean)
- **Traitement** : Sélectionnez le relais contrôlant le système de traitement (switch ou input_boolean)
- **Traitement 2** (optionnel) : Sélectionnez un second relais de traitement si nécessaire (switch ou input_boolean)
- **Surpresseur** : Sélectionnez le relais contrôlant le surpresseur (switch ou input_boolean)

> **Note** : L'intégration crée automatiquement tous les capteurs d'état et boutons de contrôle. Vous n'avez **plus besoin** de créer manuellement des input_button, input_text ou input_number dans votre configuration.yaml !

### Entités créées automatiquement

L'intégration Pool Control crée automatiquement les entités suivantes :

#### Capteurs (Sensors)

- **Status Asservissement** : Affiche l'état actuel du mode de contrôle (Actif/Auto/Inactif + Saison/Hivernage)
- **Temps de filtration** : Affiche le temps de filtration calculé
- **Planning de Filtration** : Affiche les horaires de filtration et la température de calcul
- **Status Filtration** : Affiche l'état de la filtration
- **Status Surpresseur** : Affiche l'état et le temps restant du surpresseur
- **Status Lavage Filtre** : Affiche les instructions pour le lavage du filtre à sable

#### Boutons (Buttons)

- **Reset** : Recalcule le temps de filtration
- **Actif** : Active le mode manuel (marche forcée)
- **Auto** : Active le mode automatique
- **Inactif** : Désactive le contrôle automatique
- **Saison** : Active le mode saison (température > 10°C)
- **Hivernage** : Active le mode hivernage (température < 10°C)
- **Surpresseur** : Lance le surpresseur pour la durée configurée
- **Lavage** : Lance l'assistant de lavage du filtre à sable
- **Stop** : Arrête le surpresseur ou le lavage en cours

### Configuration des options

Une fois l'intégration ajoutée, vous pouvez configurer toutes les options avancées via l'interface utilisateur :

1. Allez dans **Paramètres** → **Appareils et services**
2. Cliquez sur "Pool Control"
3. Cliquez sur **CONFIGURER**
4. Un menu de navigation vous permet d'accéder aux différentes sections de configuration :

#### Menu Utilisateur
Modification des capteurs et actionneurs configurés initialement.

#### Menu Filtration

- **Méthode de calcul** :
  - (1) Courbe de température (recommandé)
  - (2) Température / 2 (méthode classique)
- **Coefficient d'ajustement** (0.3 à 1.7) : Ajuste le temps de filtration calculé
- **Horaire pivot** (format "HH:MM") : Heure centrale de la filtration (défaut : 13:00)
- **Pause pivot** (en minutes) : Temps de coupure pendant la filtration
- **Répartition autour du pivot** :
  - (1/2 <> 1/2) : Répartition symétrique
  - (1/3 <> 2/3) : Plus de filtration l'après-midi
  - (2/3 <> 1/3) : Plus de filtration le matin
  - (1/1 <>) : Tout avant le pivot
  - (<> 1/1) : Tout après le pivot
- **Temps de filtration minimum** (en heures) : Durée minimale quotidienne

#### Menu Hivernage

- **Traitement pendant l'hivernage** : Active le traitement chimique en mode hivernage
- **Coefficient d'ajustement hivernage** (0.3 à 1.7) : Ajuste le temps de filtration en hivernage
- **Répartition horaire hivernage** : Même options que pour le mode saison
- **Choix heure filtration** :
  - (1) Lever du soleil (recommandé pour fonction hors-gel)
  - (2) Heure fixe définie
- **Horaire pivot hivernage** (format "HH:MM") : Si choix (2) sélectionné (défaut : 06:00)
- **Température de sécurité** (°C) : Seuil de déclenchement de la marche forcée hors-gel (défaut : -2°C)
- **Hystérésis température** (°C) : Évite les démarrages/arrêts intempestifs (défaut : 0.5°C)
- **Filtration 5mn/3h** : Lance la filtration 5 minutes toutes les 3 heures

#### Menu Avancé

- **Désactiver marche forcée** : Revient automatiquement en mode auto au début du cycle de filtration
- **Sonde dans local technique** : Active le mode sonde déportée
- **Pause avant relevé température** (en minutes) : Temporisation pour stabilisation de la température
- **Durée surpresseur** (en minutes) : Temps de fonctionnement du surpresseur (défaut : 5)
- **Durée lavage** (en minutes) : Temps de lavage du filtre (défaut : 2)
- **Durée rinçage** (en minutes) : Temps de rinçage du filtre (défaut : 2)

### Principe de fonctionnement

#### Mode Saison

La filtration est calculée en fonction de la température de l'eau :
- **Méthode courbe** : Utilise une courbe optimisée pour un temps de filtration adapté
- **Méthode température/2** : Divise la température par 2 (ex : 24°C → 12h de filtration)

Le temps de filtration est réparti autour de l'horaire pivot configuré selon la distribution choisie.

#### Mode Hivernage

La filtration démarre 2 heures avant le lever du soleil (ou à l'heure configurée) pour un minimum de 3 heures.
- Si température eau > 9°C : temps calculé = température / 3
- Si température air < seuil sécurité : filtration en continu (hors-gel)
- Option filtration 5mn/3h disponible pour circulation régulière

#### Sonde dans local technique

Si votre sonde de température est située dans le local technique :
- La température n'est prise en compte que pendant la filtration
- Une pause configurable permet d'attendre que l'eau circule et que la sonde reflète la température du bassin

### Exemple de carte pour le tableau de bord

![DashBoard](https://github.com/scadinot/pool_control/blob/main/img/dashboard.png)

Voici un exemple de carte utilisant les nouvelles entités créées automatiquement :

```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.votre_temperature_eau
        name: Température Eau
      - type: entity
        entity: sensor.votre_temperature_air
        name: Température Air
  - type: entity
    entity: sensor.pool_control_filtration_time
    name: Temps filtration
  - type: entity
    entity: sensor.pool_control_filtration_schedule
    name: Planning
  - type: button
    show_name: true
    show_icon: true
    tap_action:
      action: call-service
      service: button.press
      target:
        entity_id: button.pool_control_reset
    name: Reset
    icon: mdi:restart
  - type: entity
    entity: sensor.pool_control_asservissement_status
    name: État
  - type: horizontal-stack
    cards:
      - type: button
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.pool_control_actif
        name: Actif
        icon: mdi:play-circle
      - type: button
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.pool_control_auto
        name: Auto
        icon: mdi:auto-fix
      - type: button
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.pool_control_inactif
        name: Inactif
        icon: mdi:stop-circle
  - type: horizontal-stack
    cards:
      - type: button
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.pool_control_saison
        name: Saison
        icon: mdi:weather-sunny
      - type: button
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.pool_control_hivernage
        name: Hivernage
        icon: mdi:snowflake
  - type: entity
    entity: sensor.pool_control_surpresseur_status
    name: Surpresseur
  - type: button
    tap_action:
      action: call-service
      service: button.press
      target:
        entity_id: button.pool_control_surpresseur
    name: Surpresseur
    icon: mdi:pump
  - type: entity
    entity: sensor.pool_control_filtre_sable_lavage_status
    name: Lavage
  - type: button
    tap_action:
      action: call-service
      service: button.press
      target:
        entity_id: button.pool_control_lavage
    name: Lavage
    icon: mdi:air-filter
  - type: button
    tap_action:
      action: call-service
      service: button.press
      target:
        entity_id: button.pool_control_stop
    name: Stop
    icon: mdi:stop
```

## Surpresseur

Pour activer le surpresseur, appuyez sur le bouton **Surpresseur**. Le surpresseur est alors lancé pour la durée configurée.

Si la filtration n'est pas active, elle sera lancée automatiquement, puis le surpresseur après une temporisation de quelques secondes. Cette temporisation permet d'éviter d'endommager le surpresseur en mettant en mouvement l'eau dans le circuit de filtration.

Le capteur **Status Surpresseur** affiche le temps restant sous forme de compte à rebours.

À la fin, le surpresseur s'arrête ainsi que la filtration si elle n'était pas active auparavant.
Le bouton **Stop** permet d'arrêter le cycle avant la fin si nécessaire.

## Nettoyage du filtre à sable

Cette fonctionnalité est un assistant pour vous guider dans les opérations de lavage de votre filtre à sable.

Pour lancer le lavage, appuyez sur **Lavage**. La filtration est alors stoppée et le capteur **Status Lavage Filtre** affiche :

`[Arrêt, position lavage]`

Comme demandé, positionnez votre vanne sur la position **Lavage**, puis appuyez à nouveau sur **Lavage**.

![Position Lavage](https://github.com/scadinot/pool_control/blob/main/img//position-lavage.png)

La filtration démarre, le capteur affiche alors le temps restant pour l'opération de lavage :

`[Lavage : xx]`

![Schema Lavage](https://github.com/scadinot/pool_control/blob/main/img//schema-lavage.gif)

À la fin du lavage, le capteur affiche le message suivant:

`[Arrêt, position rinçage]`

Comme demandé, positionnez votre vanne sur la position **Rinçage**, puis appuyez à nouveau sur **Lavage**.

![Position Rinçage](https://github.com/scadinot/pool_control/blob/main/img//position-rincage.png)

La filtration démarre, le capteur affiche alors le temps restant pour l'opération de rinçage :

`[Rinçage : xx]`

![Schema Rinçage](https://github.com/scadinot/pool_control/blob/main/img//schema-rincage.gif)

À la fin du rinçage, le capteur affiche le message suivant :

`[Filtration]`

Comme demandé, positionnez votre vanne sur la position **Filtration**, puis appuyez à nouveau sur **Lavage**.

![Position Filtration](https://github.com/scadinot/pool_control/blob/main/img/position-filtration.png)

Si la filtration était active avant l'opération de lavage, elle redémarre automatiquement.

![Schema Filtration](https://github.com/scadinot/pool_control/blob/main/img/schema-filtration.gif)

Pendant les différentes opérations de nettoyage du filtre à sable, le bouton **Stop** permet d'arrêter l'opération en cours.

## Migration depuis l'ancienne version

Si vous utilisez actuellement Pool Control avec configuration via `configuration.yaml`, vous pouvez migrer vers la nouvelle version avec Config Flow :

1. **Sauvegardez** votre configuration actuelle
2. **Supprimez** la section `pool_control:` de votre `configuration.yaml`
3. **Redémarrez** Home Assistant
4. **Ajoutez** l'intégration via l'interface utilisateur comme décrit ci-dessus
5. **Supprimez** les anciennes entités `input_button`, `input_text` et `input_number` que vous aviez créées manuellement (elles ne sont plus nécessaires)
6. **Mettez à jour** votre tableau de bord pour utiliser les nouvelles entités automatiques

> **Astuce** : Notez vos paramètres de configuration avant la migration pour pouvoir les ressaisir facilement via l'interface UI.

## Support

Pour signaler un bug ou demander une fonctionnalité, ouvrez une issue sur [GitHub](https://github.com/scadinot/pool_control/issues).
