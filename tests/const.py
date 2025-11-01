"""Constantes pour les tests Pool Control."""

# Configuration minimale pour les tests
MOCK_CONFIG_MINIMAL = {
    "temperatureWater": "sensor.pool_temperature",
    "temperatureOutdoor": "sensor.outdoor_temperature",
    "leverSoleil": "sensor.sun_next_rising",
    "filtration": "switch.pool_filtration",
}

# Configuration complète pour les tests
MOCK_CONFIG_FULL = {
    # Capteurs
    "temperatureWater": "sensor.pool_temperature",
    "temperatureOutdoor": "sensor.outdoor_temperature",
    "leverSoleil": "sensor.sun_next_rising",

    # Boutons
    "buttonReset": "input_button.reset",
    "buttonActif": "input_button.asservissement_actif",
    "buttonAuto": "input_button.asservissement_auto",
    "buttonInactif": "input_button.asservissement_inactif",
    "buttonSaison": "input_button.mode_saison",
    "buttonHivernage": "input_button.mode_hivernage",
    "buttonSurpresseur": "input_button.surpresseur",
    "buttonLavage": "input_button.lavage_filtre_sable",
    "buttonStop": "input_button.stop",

    # Actionneurs
    "filtration": "switch.pool_filtration",
    "traitement": "switch.pool_treatment",
    "traitement_2": "switch.pool_treatment_2",
    "surpresseur": "switch.pool_booster",

    # Options
    "disableMarcheForcee": False,
    "methodeCalcul": 1,
    "datePivot": "13:00",
    "pausePivot": 0,
    "distributionDatePivot": 2,
    "coefficientAjustement": 1.0,
    "sondeLocalTechnique": True,
    "sondeLocalTechniquePause": 5,
    "traitementHivernage": True,
    "tempsDeFiltrationMinimum": 3,
    "choixHeureFiltrationHivernage": 1,
    "datePivotHivernage": "06:00",
    "temperatureSecurite": 0,
    "temperatureHysteresis": 0.5,
    "filtration5mn3h": True,
    "surpresseurDuree": 5,
    "lavageDuree": 2,
    "rincageDuree": 2,
}

# Entity IDs pour les mocks
ENTITY_POOL_TEMPERATURE = "sensor.pool_temperature"
ENTITY_OUTDOOR_TEMPERATURE = "sensor.outdoor_temperature"
ENTITY_SUN_NEXT_RISING = "sensor.sun_next_rising"
ENTITY_FILTRATION = "switch.pool_filtration"
ENTITY_TREATMENT = "switch.pool_treatment"
ENTITY_TREATMENT_2 = "switch.pool_treatment_2"
ENTITY_BOOSTER = "switch.pool_booster"
