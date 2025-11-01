# GitHub Actions Workflows

Ce dossier contient les workflows GitHub Actions pour l'intégration continue (CI/CD) de Pool Control.

## 🔄 Workflows Disponibles

### 1. Tests (`tests.yaml`)

**Déclenchement** :
- À chaque push sur `main`
- À chaque Pull Request vers `main`
- Manuellement via l'interface GitHub Actions

**Actions** :
- Exécute tous les tests pytest
- Teste sur Python 3.11 et 3.12
- Exécute les tests par marqueur (unit, integration, bugs)
- Vérifie la qualité du code avec ruff

**Badge** : [![Tests](https://github.com/scadinot/pool_control/actions/workflows/tests.yaml/badge.svg)](https://github.com/scadinot/pool_control/actions/workflows/tests.yaml)

### 2. Validate HACS (`Validate HACS.yaml`)

**Déclenchement** :
- À chaque push
- À chaque Pull Request
- Quotidiennement (cron)
- Manuellement

**Actions** :
- Valide que l'intégration est compatible HACS

**Badge** : [![HACS](https://github.com/scadinot/pool_control/actions/workflows/Validate%20HACS.yaml/badge.svg)](https://github.com/scadinot/pool_control/actions/workflows/Validate%20HACS.yaml)

### 3. Validate Hassfest (`Validate Hassfest.yaml`)

**Déclenchement** :
- À chaque push
- À chaque Pull Request

**Actions** :
- Valide que l'intégration respecte les standards Home Assistant

**Badge** : [![Hassfest](https://github.com/scadinot/pool_control/actions/workflows/Validate%20Hassfest.yaml/badge.svg)](https://github.com/scadinot/pool_control/actions/workflows/Validate%20Hassfest.yaml)

## 📊 Visualisation des Tests

### Sur GitHub

1. Allez sur l'onglet **Actions** du repository
2. Sélectionnez le workflow **Tests**
3. Cliquez sur un run pour voir les détails

### Badges dans le README

Les badges affichent automatiquement l'état des workflows :
- ✅ Vert : Tous les tests passent
- ❌ Rouge : Des tests échouent
- 🟡 Jaune : En cours d'exécution

## 🔧 Exécution Manuelle

Pour lancer les tests manuellement :

1. Allez sur **Actions** → **Tests**
2. Cliquez sur **Run workflow**
3. Sélectionnez la branche
4. Cliquez sur **Run workflow**

## 📝 Détails du Workflow Tests

### Matrice de Tests

Les tests s'exécutent sur :
- **Python 3.11**
- **Python 3.12**

### Étapes

1. **Checkout** : Récupère le code
2. **Setup Python** : Configure Python
3. **Install dependencies** : Installe les dépendances de test
4. **Run tests** : Exécute pytest avec verbose
5. **Run tests with markers** : Tests par catégorie

### Commandes Exécutées

```bash
# Installation
pip install -r requirements_test.txt

# Tests complets
pytest tests/ -v --tb=short

# Tests par marqueur
pytest -m unit -v
pytest -m integration -v
pytest -m bugs -v
```

## 🎯 Prochaines Améliorations

- [ ] Ajout de la couverture de code (coverage)
- [ ] Upload des rapports de couverture vers Codecov
- [ ] Tests de performance
- [ ] Tests d'intégration avec Home Assistant complet

## 📚 Documentation

- [GitHub Actions](https://docs.github.com/en/actions)
- [pytest documentation](https://docs.pytest.org/)
- [Home Assistant CI/CD](https://developers.home-assistant.io/docs/creating_integration_continuous_integration)
