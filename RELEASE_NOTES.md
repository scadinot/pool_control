# Release Notes v0.0.14 - Installation moderne via Config Flow 🎉

## 🎉 Points forts de cette release

### Installation moderne via Config Flow
Plus besoin de modifier le fichier `configuration.yaml` ! L'installation se fait maintenant entièrement via l'interface utilisateur de Home Assistant.

### Création automatique des entités
L'intégration crée automatiquement **15 entités** lors de l'installation :
- **6 capteurs** d'état et de monitoring
- **9 boutons** de contrôle et de configuration

### 100% de tests réussis ✅
Les **350 tests unitaires** passent tous avec succès, garantissant la fiabilité et la stabilité de l'intégration.

---

## 📦 Nouveautés

### Ajouts
- ✅ **Création automatique de 6 capteurs d'état** :
  - `sensor.status_asservissement` - État du mode d'asservissement (Actif/Auto/Inactif)
  - `sensor.temps_de_filtration` - Temps de filtration calculé en heures
  - `sensor.planning_de_filtration` - Planning des périodes de filtration
  - `sensor.status_filtration` - État de la pompe de filtration
  - `sensor.status_surpresseur` - État du surpresseur
  - `sensor.status_lavage_filtre` - État du lavage du filtre

- ✅ **Création automatique de 9 boutons de contrôle** :
  - `button.pool_control_reset` - Réinitialisation complète
  - `button.pool_control_actif` - Passer en mode Actif
  - `button.pool_control_auto` - Passer en mode Auto
  - `button.pool_control_inactif` - Passer en mode Inactif
  - `button.pool_control_saison` - Activer le mode Saison
  - `button.pool_control_hivernage` - Activer le mode Hivernage
  - `button.pool_control_surpresseur` - Activer le surpresseur
  - `button.pool_control_lavage` - Lancer le lavage du filtre
  - `button.pool_control_stop` - Arrêt d'urgence

- ✅ **CHANGELOG.md** avec historique complet des versions (v0.0.9 à v0.0.14)
- ✅ **Guide de migration** pour les utilisateurs de versions antérieures

### Modifications

- ⚠️ **CHANGEMENT MAJEUR** : L'installation se fait maintenant via **Config Flow UI**
  - Plus besoin de modifier `configuration.yaml`
  - Configuration complète via l'interface utilisateur
  - Les boutons ne doivent plus être définis manuellement (créés automatiquement)

- 📝 **Documentation complètement réécrite** :
  - README.md avec instructions d'installation Config Flow
  - info.md mis à jour pour l'affichage dans HACS
  - ANALYSIS.md avec métriques complètes v0.0.14

### Documentation

- 📖 **Guide complet d'installation** via l'interface utilisateur
- 📖 **Liste détaillée** de toutes les entités auto-créées avec descriptions
- 📖 **4 menus de configuration des options** :
  1. Calcul de filtration (méthode, heure pivot, coefficient)
  2. Sonde local technique (activation et pause)
  3. Hivernage (traitement, heure de filtration, température)
  4. Équipements (durées surpresseur, lavage, rinçage)
- 📖 **Instructions de migration** depuis les versions antérieures

---

## 🔄 Migration depuis l'ancienne version

Si vous utilisez une version antérieure (0.0.13 ou inférieure) avec configuration YAML :

1. **Sauvegardez** votre configuration actuelle dans `configuration.yaml`
2. **Supprimez** la section `pool_control:` de `configuration.yaml`
3. **Supprimez** tous les `input_button` créés manuellement pour Pool Control
4. **Redémarrez** Home Assistant
5. **Ajoutez** l'intégration via : Paramètres → Appareils et services → Ajouter une intégration → Pool Control
6. **Sélectionnez** vos entités existantes (températures, relais)
7. **C'est tout !** Les boutons et capteurs sont créés automatiquement

> **Note** : Vous devrez mettre à jour vos dashboards pour utiliser les nouvelles entités avec le préfixe `button.pool_control_*` et `sensor.*_*`

Consultez le README.md pour plus de détails sur la migration.

---

## 📊 Statistiques

- **350 tests unitaires** - 100% de réussite ✅
- **65% de couverture de code** (+65% par rapport à v0.0.12)
- **Ratio Test/Code : 2.3:1** - 5432 lignes de tests pour 2362 lignes de code
- **19 fichiers Python** - Architecture modulaire avec 11 mixins
- **3 workflows CI/CD** - Tests automatisés, validation HACS et Hassfest

---

## 🔗 Liens utiles

- [CHANGELOG complet](https://github.com/scadinot/pool_control/blob/main/CHANGELOG.md)
- [Documentation complète (README)](https://github.com/scadinot/pool_control/blob/main/README.md)
- [Rapport d'analyse technique (ANALYSIS)](https://github.com/scadinot/pool_control/blob/main/ANALYSIS.md)
- [Issues et support](https://github.com/scadinot/pool_control/issues)

---

**Installation via HACS recommandée** - Le tag v0.0.14 est disponible et HACS proposera automatiquement la mise à jour.

Merci d'utiliser Pool Control ! 🏊‍♂️
