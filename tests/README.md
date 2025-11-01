# Tests Unitaires Pool Control

Ce dossier contient les tests unitaires pour le composant Pool Control de Home Assistant.

## 🚀 Installation

```bash
# Installer les dépendances de test
pip install -r requirements_test.txt
```

## 🧪 Exécuter les Tests

### Tous les tests

```bash
pytest
```

### Tests avec couverture

```bash
pytest --cov=custom_components.pool_control --cov-report=html
```

Le rapport HTML sera généré dans `htmlcov/index.html`

### Tests spécifiques

```bash
# Un fichier
pytest tests/test_environment.py

# Une classe
pytest tests/test_environment.py::TestEnvironmentSetup

# Un test précis
pytest tests/test_environment.py::TestEnvironmentSetup::test_pytest_works
```

### Tests par marqueur

```bash
# Tests unitaires rapides
pytest -m unit

# Tests de non-régression
pytest -m bugs

# Tests d'intégration
pytest -m integration
```

### Mode verbeux

```bash
# Afficher plus de détails
pytest -v

# Afficher les prints
pytest -s

# Arrêter au premier échec
pytest -x
```

## 📁 Structure

```
tests/
├── __init__.py              # Package Python
├── conftest.py              # Fixtures communes
├── const.py                 # Constantes pour tests
├── README.md                # Cette documentation
│
├── test_environment.py      # Tests de validation
├── test_bugs_regression.py  # Tests non-régression (TODO)
├── test_activation.py       # Tests activation (TODO)
└── ...                      # Autres tests (TODO)
```

## 🔧 Fixtures Disponibles

### `mock_hass`
Mock de Home Assistant avec services et états mockés.

```python
def test_example(mock_hass):
    mock_hass.states.get("sensor.test")
    mock_hass.services.async_call("switch", "turn_on", {})
```

### `mock_pool_config`
Configuration complète pour les tests.

```python
def test_example(mock_pool_config):
    assert mock_pool_config["filtration"] == "switch.pool_filtration"
```

### `mock_state_factory`
Factory pour créer des états mockés.

```python
def test_example(mock_state_factory):
    state = mock_state_factory("sensor.temp", "25.5")
    assert state.state == "25.5"
```

### `setup_hass_states`
Helper pour configurer plusieurs états.

```python
def test_example(mock_hass, setup_hass_states):
    setup_hass_states({
        "switch.filtration": "on",
        "sensor.temperature": "25.5",
    })
```

## 📊 Couverture de Code

Objectif : **>70%**

Vérifier la couverture :
```bash
pytest --cov=custom_components.pool_control --cov-report=term-missing
```

## 🏷️ Marqueurs

- `@pytest.mark.unit` : Tests unitaires rapides
- `@pytest.mark.integration` : Tests d'intégration
- `@pytest.mark.bugs` : Tests de non-régression
- `@pytest.mark.slow` : Tests lents

## 📝 Bonnes Pratiques

1. **Un test = une assertion principale**
2. **Noms descriptifs** : `test_should_activate_when_temperature_high`
3. **AAA Pattern** : Arrange, Act, Assert
4. **Utiliser les fixtures** pour éviter la duplication
5. **Tests async** : Utiliser `@pytest.mark.asyncio`

## 🔍 Debug

```bash
# Afficher les tests sans les exécuter
pytest --collect-only

# Afficher les fixtures disponibles
pytest --fixtures

# Mode debug avec pdb
pytest --pdb
```

## 📈 CI/CD

Les tests sont exécutés automatiquement via GitHub Actions sur chaque PR.

Configuration : `.github/workflows/test.yaml` (TODO)
