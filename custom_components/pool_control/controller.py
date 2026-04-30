"""Pool controller integration for Home Assistant."""

import logging
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .activation import ActivationMixin
from .buttons import ButtonMixin
from .filtration import FiltrationMixin
from .hivernage import HivernageMixin
from .lavage import LavageMixin
from .saison import SaisonMixin
from .scheduler import SchedulerMixin
from .sensors import SensorMixin
from .service import ServiceMixin
from .surpresseur import SurpresseurMixin
from .traitement import TraitementMixin
from .utils import FiltrationUtilsMixin

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1
STORAGE_KEY = "pool_control_data"
STORAGE_KEY_PREFIX = "pool_control_data"

VALID_DISTRIBUTIONS = (1, 2, 3, 4, 5)


def _validate_distribution(value: Any, name: str, default: int) -> int:
    """Validate that a distribution config value is in the allowed range.

    Returns the value as int if valid (1..5), otherwise logs a warning
    and returns the provided default. Handles None and non-int values.
    """

    try:
        v = int(value)
        if v in VALID_DISTRIBUTIONS:
            return v
    except (TypeError, ValueError):
        pass

    _LOGGER.warning(
        "%s invalide (%s), utilisation de la valeur par défaut %s",
        name,
        value,
        default,
    )
    return default


class PoolController(
    ActivationMixin,
    ButtonMixin,
    FiltrationMixin,
    HivernageMixin,
    LavageMixin,
    SaisonMixin,
    SchedulerMixin,
    SensorMixin,
    ServiceMixin,
    SurpresseurMixin,
    TraitementMixin,
    FiltrationUtilsMixin,
):
    """Pool controller for managing pool automation logic."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict,
        entry: Optional[ConfigEntry] = None,
    ) -> None:
        """Initialize the pool controller."""

        # Initialisation de la classe mère
        # On appelle le constructeur de la classe mère pour initialiser les mixins
        super().__init__()

        # configuration.yaml
        self.hass = hass
        self.entry = entry
        # Store distinct par instance afin de cohabiter en multi-instance ;
        # une instance unique conserve la clé historique pour la rétro-compat.
        storage_key = (
            f"{STORAGE_KEY_PREFIX}_{entry.entry_id}" if entry is not None else STORAGE_KEY
        )
        self.store = Store(hass, STORAGE_VERSION, storage_key)
        self.data = {}
        self.initialized = False

        # Configuration capteurs
        self.temperatureWater = config.get("temperatureWater")
        self.temperatureOutdoor = config.get("temperatureOutdoor")
        self.leverSoleil = config.get("leverSoleil")

        # Entités
        self.filtration = config.get("filtration")
        self.traitement = config.get("traitement")
        self.traitement_2 = config.get("traitement_2")
        self.surpresseur = config.get("surpresseur")

        # réglages personnalisés
        self.surpresseurDuree = config.get("surpresseurDuree", 5)

        self.disableMarcheForcee = config.get("disableMarcheForcee", False)
        self.methodeCalcul = int(config.get("methodeCalcul", 1))
        self.datePivot = config.get("datePivot", "13:00")
        self.pausePivot = config.get("pausePivot", 0)
        self.distributionDatePivot = _validate_distribution(
            config.get("distributionDatePivot", 1), "distributionDatePivot", 1
        )
        self.coefficientAjustement = config.get("coefficientAjustement", 1.0)
        self.coefficientAjustementHivernage = config.get(
            "coefficientAjustementHivernage", 1.0
        )

        self.sondeLocalTechnique = config.get("sondeLocalTechnique", False)
        self.sondeLocalTechniquePause = config.get("sondeLocalTechniquePause", 0)
        self.traitementHivernage = config.get("traitementHivernage", False)
        self.tempsDeFiltrationMinimum = config.get("tempsDeFiltrationMinimum", 3)
        self.distributionDatePivotHivernage = _validate_distribution(
            config.get("distributionDatePivotHivernage", 4),
            "distributionDatePivotHivernage",
            4,
        )
        self.choixHeureFiltrationHivernage = config.get(
            "choixHeureFiltrationHivernage", 1
        )
        self.datePivotHivernage = config.get("datePivotHivernage", "06:00")
        self.temperatureSecurite = config.get("temperatureSecurite", -2)
        self.temperatureHysteresis = config.get("temperatureHysteresis", 0.5)
        self.filtration5mn3h = config.get("filtration5mn3h", False)

        self.lavageDuree = config.get("lavageDuree", 2)
        self.rincageDuree = config.get("rincageDuree", 2)

    async def async_initialize(self) -> None:
        """Initialise PoolController by loading data from store."""

        raw_data = await self.store.async_load()

        if raw_data:
            self.data = raw_data
            _LOGGER.info("Loaded data from store: %s", self.data)
        else:
            _LOGGER.info("No data found in store")

        self.initialized = True

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_save_data)

    async def async_save_data(self, event: Optional[Any] = None) -> None:
        """Save the current data to the store."""

        if self.initialized:
            await self.store.async_save(self.data)
            if event is not None:
                _LOGGER.info("Saved data to store: %s", self.data)

    def set_data(self, key: str, value: Any) -> None:
        """Set data in the store and trigger save if changed."""

        oldValue = self.data.get(key)
        self.data[key] = value

        if oldValue != value:
            self.hass.async_create_task(self.async_save_data())

    def get_data(self, key: str, default: Optional[Any] = None) -> Any:
        """Get data from the store, returning default if not found."""

        return self.data.get(key, default)
