# Pool Control

_Composant Home Assistant permettant de gérer la filtration d'une piscine en fonction de la température._

## ✨ Nouveautés v0.0.15

- **Type hints à 100%** - Toutes les fonctions sont annotées pour une meilleure qualité de code
- **Installation moderne via Config Flow** - Configuration 100% via l'interface utilisateur
- **Création automatique des entités** - 6 capteurs et 9 boutons créés automatiquement

## Fonctionnalités

- Calcul automatique du temps de filtration selon la température
- Gestion des modes : Actif, Auto, Inactif
- Modes saisonniers : Saison et Hivernage actif
- Support filtre à sable avec lavage automatique
- Surpresseur pour robot nettoyeur
- Interface de configuration avancée avec 4 menus d'options

## Installation

1. Cliquez sur **TÉLÉCHARGER** dans HACS
2. Redémarrez Home Assistant
3. Allez dans **Paramètres** → **Appareils et services** → **Ajouter une intégration**
4. Recherchez **Pool Control**
5. Sélectionnez vos entités existantes (température eau, température extérieure, lever du soleil, relais filtration, etc.)

**C'est tout !** L'intégration crée automatiquement tous les capteurs d'état et boutons de contrôle.

## Entités créées automatiquement

### 6 Capteurs
- `sensor.pool_control_asservissement_status` - État du mode d'asservissement
- `sensor.pool_control_filtration_time` - Temps de filtration calculé
- `sensor.pool_control_filtration_schedule` - Planning des périodes de filtration
- `sensor.pool_control_filtration_status` - État de la pompe de filtration
- `sensor.pool_control_surpresseur_status` - État du surpresseur
- `sensor.pool_control_filtre_sable_lavage_status` - État du lavage du filtre

### 9 Boutons
- `button.pool_control_reset` - Réinitialisation
- `button.pool_control_actif` - Mode Actif
- `button.pool_control_auto` - Mode Auto
- `button.pool_control_inactif` - Mode Inactif
- `button.pool_control_saison` - Mode Saison
- `button.pool_control_hivernage` - Mode Hivernage
- `button.pool_control_surpresseur` - Activation surpresseur
- `button.pool_control_lavage` - Lavage filtre à sable
- `button.pool_control_stop` - Arrêt d'urgence

## Configuration des options

Après installation, configurez les options avancées via **Appareils et services** → **Pool Control** → **Configurer** :

1. **Calcul de filtration** - Méthode de calcul, heure pivot, coefficient d'ajustement
2. **Sonde local technique** - Activation et pause
3. **Hivernage** - Traitement, heure de filtration, température de sécurité
4. **Équipements** - Durées pour surpresseur, lavage et rinçage

## Migration depuis l'ancienne version

Si vous utilisez une version antérieure avec `configuration.yaml`, consultez le [README.md](https://github.com/scadinot/pool_control/blob/main/README.md) pour les instructions de migration.

## Documentation complète

Veuillez lire le fichier [README.md](https://github.com/scadinot/pool_control/blob/main/README.md) pour plus de détails.
