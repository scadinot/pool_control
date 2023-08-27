# Pool Control

_Composant Home Assistant permettant de gérer la filtration d'une piscine en fonction de la température._

## Fonctionnalitées

- Hivernage actif.
- Filtre à sable.
- Surpresseur pour robot nettoyeur.

## Installation

### Installation HACS

1. Installez [HACS] (https://hacs.xyz/). Vous recevrez ainsi les mises à jour automatiquement.
2. Ajoutez ce dépôt Github comme dépôt personnalisé dans les paramètres de HACS.
3. recherchez et installez "Pool Control" dans HACS et cliquez sur `TÉLÉCHARGER`.
4. Modifiez votre `configuration.yaml` comme expliqué ci-dessous.
5. Redémarrez Home Assistant.

### Installation manuelle

1. En utilisant l'outil de votre choix, ouvrez le répertoire (dossier) de votre configuration HA (où vous trouverez `configuration.yaml`).
2. Si vous n'avez pas de répertoire (dossier) `custom_components`, vous devez le créer.
3. Dans le répertoire (dossier) `custom_components`, créez un nouveau dossier appelé `pool_control`.
4. Téléchargez _tous_ les fichiers du répertoire (dossier) `custom_components/pool_control/` de ce dépôt Github.
5. Placez les fichiers que vous avez téléchargés dans le nouveau répertoire (dossier) que vous avez créé.
6. Modifiez votre `configuration.yaml` comme expliqué ci-dessous
7. Redémarrez Home Assistant

## Configuration

Ajoutez au fichier configuration.yaml les éléments suivants :

```yaml

pool_control:

  temperatureWater: input_number.temperaturewater       # Capteur de température de l'eau
  temperatureOutdoor: input_number.temperatureoudoor    # Capteur de température de l'air
  leverSoleil: sensor.sun_next_rising                   # Sensor de l'heure de lever du soleil

  buttonReset: input_button.reset
  buttonSurpresseur: input_button.surpresseur
  buttonLavage: input_button.lavage_filtre_sable
  buttonStop: input_button.stop

  buttonActif: input_button.asservissement_actif
  buttonAuto: input_button.asservissement_auto
  buttonInactif: input_button.asservissement_inactif

  buttonSaison: input_button.mode_saison
  buttonHivernage: input_button.mode_hivernage

  filtration: input_boolean.filtration                  # Relais de filtration
  traitement: input_boolean.traitement                  # Relais de traitement
  surpresseur: input_boolean.surpresseur                # Relais de surpresseur

  # optionnel:

  disableMarcheForcee: False
  methodeCalcul: 1                                      # 1:Curve | 2:TemperatureReducedByHalf
  datePivot: "13:00"
  pausePivot: 0
  distributionDatePivot: 2                              # 1:(1/2 <> 1/2) | 2:(1/3 <> 2/3)
  coefficientAjustement: 1.0                            # 0.3 <> 1.7
  sondeLocalTechnique: True                             # True | False
  sondeLocalTechniquePause: 5
  traitementHivernage: True                             # True | False
  tempsDeFiltrationMinimum: 3
  choixHeureFiltrationHivernage: 1                      # 1:(lever_soleil) | 2:(datePivotHivernage)
  datePivotHivernage: "06:00"
  temperatureSecurite: 0
  temperatureHysteresis: 0.5
  filtration5mn3h: True
  
  surpresseurDuree: 5

  lavageDuree: 2
  rincageDuree: 2
  
```

Tous les paramètres sont obligatoires sauf ceux après le commentaire # optionnel.

Vous devrez définir des boutons (input_button) pour l'utiliser. 

Voici un exemple de configuration à créer sur votre tableau de bord

![DashBoard](https://github.com/scadinot/pool_control/blob/main/img/dashboard.png)

Sur cette carte sont indiqués :

- `Température Eau` _mesurée par la sonde de température_
- `Température Air` _mesurée par une sonde exterieure, en l'absence de sonde vous pouvez reprendre une donnée météo_
- `Température Calcul` _suivant l'option 'sondeLocalTechnique' cette valeur sera mise à jour uniquement en cas de filtration_
- `Temps de filtration` _temps de filtration calculé par le composant_
- `L'horaire de filtration et la température utilisée pour le calcul`
- `Bouton [Reset]` _permettant de recalculer le temps de filtration_
- `L'état de l'intégration` 'Auto / Saison' .
- `Une série de boutons [Actif], [Auto], [Inactif]` _permettant de changer l'état du composant
- `Une série de boutons [Saison], [Hivernage]` _permettant de basculer du mode Saison au mode Hivernage_
- `Un affichage de l'état du surpresseur` _indiquant le temps restant pendant le fonctionnement du surpresseur_
- `Un bouton [Surpresseur]` de lancement du surpresseur.
- `Un affichage de l'état du lavage du filtre à sable` _indiquant les opérations à effectuer avec la vanne 6 voies pendant les opérations de lavage / contre lavage_
- `Un bouton [Lavage]` _de lancement du nettoyage du filtre à sable_
- `Un bouton [Stop]` _permettant d'arrêter le surpresseur ou le lavage du filtre à sable_

```yaml

type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: entity
        entity: input_number.temperaturewater
        icon: ' '
        name: Température Eau
      - type: entity
        entity: input_number.temperatureoudoor
        icon: ' '
        name: Température Air
  - type: horizontal-stack
    cards:
      - type: entity
        entity: input_number.temperaturedisplay
        icon: ' '
        name: Température Calcul
      - type: entity
        entity: input_text.filtrationtime
        icon: ' '
        name: Temps filtration
  - type: entity
    entity: input_text.filtrationschedule
    name: ' '
    icon: ' '
  - type: button
    show_name: true
    show_icon: true
    tap_action:
      action: toggle
    entity: input_button.reset
    name: Reset
    icon: mdi:button-pointer
    icon_height: 20px
  - type: entity
    entity: input_text.asservissementstatus
    icon: ' '
    name: ' '
  - type: horizontal-stack
    cards:
      - type: button
        show_name: true
        show_icon: true
        tap_action:
          action: toggle
        entity: input_button.asservissement_actif
        name: Actif
        icon: ''
        icon_height: 20px
      - type: button
        show_name: true
        show_icon: true
        tap_action:
          action: toggle
        entity: input_button.asservissement_auto
        name: Auto
        icon: ''
        icon_height: 20px
      - type: button
        show_name: true
        show_icon: true
        tap_action:
          action: toggle
        entity: input_button.asservissement_inactif
        name: Inactif
        icon: ''
        icon_height: 20px
        show_state: false
  - type: horizontal-stack
    cards:
      - type: button
        show_name: true
        show_icon: true
        tap_action:
          action: toggle
        entity: input_button.mode_saison
        name: Saison
        icon: ''
        icon_height: 20px
      - type: button
        show_name: true
        show_icon: true
        tap_action:
          action: toggle
        entity: input_button.mode_hivernage
        name: Hivernage
        icon: ''
        icon_height: 20px
  - type: entity
    entity: input_text.surpresseurstatus
    icon: ' '
    name: ' '
  - type: button
    show_name: true
    show_icon: true
    tap_action:
      action: toggle
    entity: input_button.surpresseur
    name: Surpresseur
    show_state: false
    icon_height: 20px
    icon: mdi:button-pointer
  - type: entity
    entity: input_text.filtresablelavagestatus
    icon: ' '
    name: ' '
  - type: button
    show_name: true
    show_icon: true
    tap_action:
      action: toggle
    entity: input_button.lavage_filtre_sable
    name: Lavage
    icon: mdi:button-pointer
    icon_height: 20px
  - type: button
    show_name: true
    show_icon: true
    tap_action:
      action: toggle
    entity: input_button.stop
    name: Stop
    icon: mdi:button-pointer
    icon_height: 20px

```
