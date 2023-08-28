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

### Ajoutez au fichier configuration.yaml les éléments suivants :

```yaml

pool_control:

  # Capteurs

  temperatureWater: input_number.temperaturewater       # Capteur de température de l'eau
  temperatureOutdoor: input_number.temperatureoudoor    # Capteur de température de l'air
  leverSoleil: sensor.sun_next_rising                   # Sensor de l'heure de lever du soleil

  # Boutons

  buttonReset: input_button.reset

  buttonActif: input_button.asservissement_actif
  buttonAuto: input_button.asservissement_auto
  buttonInactif: input_button.asservissement_inactif

  buttonSaison: input_button.mode_saison
  buttonHivernage: input_button.mode_hivernage
  buttonSurpresseur: input_button.surpresseur
  buttonLavage: input_button.lavage_filtre_sable
  buttonStop: input_button.stop

  # Actionneurs

  filtration: input_boolean.filtration                  # Relais de filtration
  traitement: input_boolean.traitement                  # Relais de traitement
  surpresseur: input_boolean.surpresseur                # Relais de surpresseur

  # Options

  disableMarcheForcee: True
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

### Voici le détail des differentes options de configuration

```yaml
  temperatureWater: input_number.temperaturewater
```
Cette entrée vous permet d'indiquer la sonde de température d'eau de votre piscine.
Les options `sondeLocalTechnique` et `sondeLocalTechniquePause` permettront de spécifier les caractéristiques de votre sonde de température.

```yaml
  temperatureOutdoor: input_number.temperatureoudoor
```
Cette entrée vous permet d'indiquer la sonde de température de l'air, cette information est utilisée en mode `Hivernage`. 
Si vous ne disposez pas d'une sonde de température exterieure vous pouvez utiliser une donnée météo.

```yaml
  leverSoleil: sensor.sun_next_rising
```
Cette entrée vous permet d'indiquer l'heure de lever du soleil, cette information est utilisée en mode `Hivernage`. 
	
```yaml
  buttonReset: input_button.reset

  buttonActif: input_button.asservissement_actif
  buttonAuto: input_button.asservissement_auto
  buttonInactif: input_button.asservissement_inactif

  buttonSaison: input_button.mode_saison
  buttonHivernage: input_button.mode_hivernage
  buttonSurpresseur: input_button.surpresseur
  buttonLavage: input_button.lavage_filtre_sable
  buttonStop: input_button.stop
```
vous dévez definir dans Home Assistant des input_button (9) qui vous permettront de piloter le composant Pool Control

```yaml
  filtration: input_boolean.filtration
  traitement: input_boolean.traitement
  surpresseur: input_boolean.surpresseur
```
Ces entrées vous permettent d'indiquer les actionneurs qui commanderons vos équipements `filtration`, `traitement`, `surpresseur`

```yaml
  disableMarcheForcee: True
```
Désactiver marche forcée au début du cycle de filtration pour revenir au mode auto au début du cycle de filtration, afin d'éviter de laisser indéfiniment la marche forcée
	
```yaml
  methodeCalcul: 1
```
Choix méthode de calcul : vous permet de choisir entre (1) un calcul de temps de filtration basé sur une courbe ou (2) la classique formule température / 2
	
```yaml
  datePivot: "13:00"
```
Horaire pivot de filtration (au format "hh:mm") : vous permet de définir l'heure de la filtration.
	
```yaml
  pausePivot: 0
```
Temps de coupure (segmentation de la filtration en minutes) : vous permet de faire une pause pendant la filtration, cette pause est située à l'heure pivot choisie. Les heures de début et de fin de filtration sont décalées proportionnellement. 
Utilisez le bouton `[Reset]` pour visualiser et déterminer les horaires souhaités.
	
```yaml
  distributionDatePivot: 2
```
Répartition du temps de filtration autour de l'horaire pivot (1 ou 2) : vous permet de choisir la répartition de la plage de filtration autour de l'heure pivot, au choix (1) 1/2 <> 1/2 ou (2) 1/3 <> 2/3.
	
```yaml
  coefficientAjustement: 1.0
```
Ajustement du temps de filtration : vous permet d'ajuster le temps de filtration avec un coefficient variable entre 0.5 et 1.5 ce coefficient agit sur le mode courbe ou température / 2.
	
```yaml
  sondeLocalTechnique: True
  sondeLocalTechniquePause: 5
```
Sonde de température dans local technique pour ne tenir compte de la valeur renvoyée par la sonde que pendant la filtration.
Pause avant relevé de température (en minutes) temporisation pour attendre que la température de la sonde soit au niveau de la température du bassin. 
Ce délai depend de la puissance de votre pompe et de la longueur du circuit de filtration entre la piscine et la sonde.
	
```yaml
  traitementHivernage: True
  tempsDeFiltrationMinimum: 3
  choixHeureFiltrationHivernage: 1
  datePivotHivernage: "06:00"
  temperatureSecurite: 0
  temperatureHysteresis: 0.5
  filtration5mn3h: True
```
Ces différentes options sont utilisées pendant l'hivernage actif.
traitementHivernage : cette option permet d'activer le traitement pendant l'hivernage.
tempsDeFiltrationMinimum : (en heure) par défaut la filtration en mode hivernage est calculée en divisant la température de l'eau par 3 avec un temps minimum configurable.
choixHeureFiltrationHivernage : (1 ou 2) choisissez si vous souhaitez lancer la filtration (1) à l'heure de lever du soleil ou (2) à l'heure prédéfinie.
datePivotHivernage : si vous avez selectionné (2) au choix precedent, choisissez l'heure à laquelle vous souhaitez lancer la filtration en mode hivernage au format "hh:mm".
	Attention : Si vous choisissez un horaire différent de l'heure de lever du soleil la fonction hors gel de la filtration sera sans effet. 
	Cette fonction peut être utile suivant votre abonnement EDF (possibilité de faire fonctionner la filtration pendant les heures creuses.
temperatureSecurite : cette option permet de lancer la filtration en marche forcée si la température extérieure descend en dessous d'un seuil défini.
temperatureHysteresis : cette valeur permet d'éviter les marches / arrêts intempestifs lorsque le seuil de temperatureSecurite est atteint.
filtration5mn3h : si vous le souhaitez vous pouvez activer cette option qui lancera la filration pendant 5mn toutes les 3 heures.

Principe et fonctionnement de l'hivernage :

	La filtration est lancée tous les jours au minimum pendant 3 heures, la filtration démarrera 2 heures avant le lever du soleil et s'arrêtera 1 heure après le lever du soleil. 
	Si la température de l'eau est supérieure à 9°C, le temps de filtration sera calculé en divisant la température par 3 (soit par exemple 3h20 pour 10°C). 
	Le démarrage de la filtration étant dans tous les cas 2 heures avant le lever du soleil. 
	Si vous avez activé l'option Filtration 5mn toutes les 3 heures la filtration sera lancée indépendamment de toute programmation de 02h00 à 02h05, de 05h00 à 05h05, de 08h00 à 08h05, de 11h00 à 11h05, de 14h00 à 14h05, de 17h00 à 17h05, de 20h00 à 20h05, de 23h00 à 23h05. 
	L'option Filtration permanente si température extérieure inférieure à est une sécurité supplémentaire dite hors gel qui permet éventuellement de filtrer en continu dans le cas de températures très basse
	
```yaml
  surpresseurDuree: 5
```
Permet de définir le Temps de fonctionnement du surpresseur.
	
```yaml
  lavageDuree: 2
  rincageDuree: 2
```
Permet de définir définir le Temps de lavage du filtre à sable et Temps de rinçage du filtre à sable.


### Voici un exemple de configuration à créer sur votre tableau de bord Home Assistant

![DashBoard](https://github.com/scadinot/pool_control/blob/main/img/dashboard.png)

Sur cette carte sont indiqués :

- `Température Eau` _mesurée par la sonde de température_
- `Température Air` _mesurée par une sonde exterieure ou la météo_
- `Température Calcul` _suivant l'option `sondeLocalTechnique` cette valeur sera mise à jour uniquement en cas de filtration_
- `Temps de filtration` _temps de filtration calculé par le composant_
- `L'horaire de filtration et la température utilisée pour le calcul`
- Bouton `[Reset]` _permettant de recalculer le temps de filtration_
- `L'état de l'intégration` 'Auto / Saison' .
- Boutons `[Actif]`, `[Auto]`, `[Inactif]` _permettant de changer l'état du composant `Pool Control`_
- Boutons `[Saison]`, `[Hivernage]` _permettant de basculer du mode Saison au mode Hivernage_
- `L'état du surpresseur` _indiquant le temps restant pendant le fonctionnement du surpresseur_
- Bouton `[Surpresseur]` de lancement du surpresseur.
- `L'état du lavage du filtre à sable` _indiquant les opérations à effectuer avec la vanne 6 voies pendant les opérations de lavage / contre lavage_
- Bouton `[Lavage]` _de lancement du nettoyage du filtre à sable_
- Bouton `[Stop]` _permettant d'arrêter le surpresseur ou le lavage du filtre à sable_

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

## Surpresseur

Pour activer le surpresseur, cliquez sur le bouton `[Surpresseur]`, le surpresseur est alors lancé pour une durée spécifiée dans la configuration.
Si la filtration n'est pas active, elle sera lancée automatiquement, puis ensuite le surpresseur après une temporisation de quelques secondes.
Cette temporisation permet d'éviter d'endommager le surpresseur en mettant en mouvement l'eau dans le circuit de filration.

Une fois le surpresseur lancé, le composant affiche le temps restant sous forme de compte à rebours.

A la fin de la temporisation, le surpresseur s'arrête ainsi que la filtration si elle n'était pas active auparavant.
Le bouton `[Stop]` permet d'arrêter le cycle avant la fin de la temporisation si nécessaire.

## Nettoyage du filtre à sable

Cette fonctionnalité est un assistant pour vous guider dans les opérations de lavage de votre filtre à sable.

Pour lancer le lavage, cliquez sur `[Lavage]`, la filtration est alors stoppée et le composant affiche :

`[Arrêt, position lavage]`

Comme demandé sur le composant, positionnez votre vanne sur la position `[lavage]`, puis cliquez à nouveau sur [Lavage].

![Position Lavage](https://github.com/scadinot/pool_control/blob/main/img//position-lavage.png)

La filtration démarre, le composant affiche alors le temps restant pour l'opération de lavage :

`[Lavage : xx]`

![Schema Lavage](https://github.com/scadinot/pool_control/blob/main/img//schema-lavage.gif)

A la fin du lavage, le composant affiche le message suivant:

`[Arrêt, position rinçage]`

Comme demandé sur le composant, positionnez votre vanne sur la position `[Rinçage]`, puis cliquez à nouveau sur [Lavage].

![Position Rinçage](https://github.com/scadinot/pool_control/blob/main/img//position-rincage.png)

La filtration démarre, le composant affiche alors le temps restant pour l'opération de rinçage :

`[Rinçage : xx]`

![Schema Rinçage](https://github.com/scadinot/pool_control/blob/main/img//schema-rincage.gif)

A la fin du rinçage, le composant affiche le message suivant :

`[Filtration]`

Comme demandé sur le composant, positionnez votre vanne sur la position `[Filtration]`, puis cliquez à nouveau sur `[Lavage]`.

![Position Filtration](https://github.com/scadinot/pool_control/blob/main/img/position-filtration.png)

Si la filtration était active avant l’opération de lavage, elle redémarre automatiquement.

![Schema Filtration](https://github.com/scadinot/pool_control/blob/main/img/schema-filtration.gif)

Pendant les différentes opérations de nettoyage du filtre à sable le bouton `[Stop]` permet d'arrêter l'opération en cours.
