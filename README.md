# Pool Control

_Plugin permettant de gérer la filtration d'une piscine en fonction de la température._

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

Le contenu minimal de votre fichier configuration.yaml est :

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
  surpresseur: input_boolean.surpresseur              	# Relais de surpresseur

  # optional:
  
  surpresseurDuree: 5

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

  lavageDuree: 2
  rincageDuree: 2
  
```

Tous les paramètres sont obligatoires sauf ceux après le commentaire # optionnel.

Vous devrez définir boutons (input_button) pour l'utiliser. 
Veuillez lire le fichier [README.md](https://github.com/scadinot/pool_control/blob/main/README.md) pour plus de détails.
