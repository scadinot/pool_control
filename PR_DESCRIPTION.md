# Pull Request: Release v0.0.14 - Modern Config Flow Installation 🎉

## 🎉 Release v0.0.14 - Installation moderne via Config Flow

Cette release modernise complètement l'installation de Pool Control avec une configuration 100% via l'interface utilisateur.

### ✨ Points forts

- **Installation moderne via Config Flow** - Plus besoin de modifier `configuration.yaml`
- **Création automatique des entités** - 6 capteurs et 9 boutons créés automatiquement
- **100% de tests réussis** - Les 350 tests passent avec succès ✅
- **Documentation complète en français** - README, CHANGELOG, info.md mis à jour

### 📦 Changements inclus

#### Ajouts
- ✅ Création automatique de 6 capteurs d'état
- ✅ Création automatique de 9 boutons de contrôle
- ✅ CHANGELOG.md avec historique complet des versions
- ✅ Guide de migration pour utilisateurs existants

#### Modifications
- ⚠️ **RUPTURE** : Installation maintenant via Config Flow UI (plus de YAML dans configuration.yaml)
- 📝 README.md complètement réécrit avec instructions Config Flow
- 📝 info.md mis à jour pour affichage HACS
- 📝 ANALYSIS.md mis à jour avec métriques v0.0.14

#### Documentation
- 📖 Guide complet d'installation via UI
- 📖 Liste de toutes les entités auto-créées
- 📖 Description des 4 menus de configuration des options
- 📖 Instructions de migration depuis versions antérieures

### 🔧 Entités créées automatiquement

**6 Capteurs :**
- `sensor.status_asservissement` - État du mode d'asservissement
- `sensor.temps_de_filtration` - Temps de filtration calculé
- `sensor.planning_de_filtration` - Planning des périodes
- `sensor.status_filtration` - État pompe de filtration
- `sensor.status_surpresseur` - État surpresseur
- `sensor.status_lavage_filtre` - État lavage du filtre

**9 Boutons :**
- `button.pool_control_reset` - Réinitialisation
- `button.pool_control_actif` / `auto` / `inactif` - Modes d'asservissement
- `button.pool_control_saison` / `hivernage` - Modes saisonniers
- `button.pool_control_surpresseur` - Activation surpresseur
- `button.pool_control_lavage` - Lavage filtre
- `button.pool_control_stop` - Arrêt d'urgence

### 📊 Statistiques de tests

- **350 tests unitaires** - 100% de réussite ✅
- **65% de couverture de code**
- **Ratio Test/Code : 2.3:1** (5432 lignes de tests pour 2362 lignes de code)

### 🔄 Migration

Pour les utilisateurs de versions antérieures, consultez la section "Migration depuis l'ancienne version" dans le README.md.

### 📝 Fichiers modifiés

- `manifest.json` - Version bumped to 0.0.14
- `README.md` - Rewrite complet avec Config Flow
- `info.md` - Mise à jour pour HACS
- `ANALYSIS.md` - Métriques v0.0.14
- `CHANGELOG.md` - Historique complet (nouveau fichier)

### 📋 Commits inclus (8 commits)

```
3db81c0 Update info.md for v0.0.14 - Modern Config Flow for HACS
45dd85a Réécrire CHANGELOG.md en français
b6a3f49 Add CHANGELOG.md - Complete version history
46ff65f Update README.md for v0.0.14 - Modern Config Flow installation
81b3c8e Update ANALYSIS.md to reflect v0.0.14 release status
05de711 Bump version to 0.0.14
350de53 Update ANALYSIS.md to v6.1 - Correct metrics and reflect 100% test success
96590ce Update ANALYSIS.md to v6.0 with comprehensive test statistics
```

---

**Ready to merge** ✅ - Tous les tests passent, documentation complète, tag v0.0.14 publié
