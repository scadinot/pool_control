"""Options flow for Pool Management integration."""

from typing import Any, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import FlowResult
from homeassistant.helpers.selector import selector

from .controller import _validate_distribution


class PoolManagementOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestion des options de Pool Management avec menu de navigation."""

    #: Entités facultatives de l'écran « user » : second relais de
    #: traitement, pompe à chaleur et son capteur de puissance. Elles
    #: reçoivent un ``suggested_value`` plutôt qu'un ``default`` (voir
    #: ``async_step_user``) et peuvent être effacées.
    CHAMPS_OPTIONNELS = ("traitement_2", "heatPump", "heatPumpPower")

    def __init__(self) -> None:
        """Initialize the options flow."""

        self.options: dict[str, Any] = {}

    async def async_step_init(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Étape initiale de configuration des options."""

        if not self.options:
            self.options = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            return await getattr(self, f"async_step_{user_input['menu']}")()

        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "user",
                "filtration",
                "hivernage",
                "avance",
                "confirm",
            ],
        )

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Handle the user step of the options flow."""

        if user_input is not None:
            # Un champ optionnel laissé vide est absent des données
            # soumises. ``update`` ne supprimant rien, il faut le retirer
            # explicitement : sans cela une entité choisie une fois ne
            # pourrait plus jamais être effacée.
            for champ in self.CHAMPS_OPTIONNELS:
                if champ not in user_input:
                    self.options.pop(champ, None)

            self.options.update(user_input)
            return await self.async_step_init()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "temperatureWater", default=self.options.get("temperatureWater")
                    ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
                    vol.Required(
                        "temperatureOutdoor",
                        default=self.options.get("temperatureOutdoor"),
                    ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
                    vol.Required(
                        "leverSoleil", default=self.options.get("leverSoleil")
                    ): selector({"entity": {"domain": ["sensor", "input_number"]}}),
                    vol.Required(
                        "filtration", default=self.options.get("filtration")
                    ): selector({"entity": {"domain": ["switch", "input_boolean"]}}),
                    vol.Required(
                        "traitement", default=self.options.get("traitement")
                    ): selector({"entity": {"domain": ["switch", "input_boolean"]}}),
                    # Champs optionnels : ``suggested_value`` et non
                    # ``default``. Avec un ``default``, voluptuous injecte la
                    # clé absente puis la valide, et le sélecteur d'entité
                    # refuse ``None`` — le champ optionnel devient alors
                    # impossible à laisser vide.
                    vol.Optional(
                        "traitement_2",
                        description={
                            "suggested_value": self.options.get("traitement_2")
                        },
                    ): selector({"entity": {"domain": ["switch", "input_boolean"]}}),
                    vol.Required(
                        "surpresseur", default=self.options.get("surpresseur")
                    ): selector({"entity": {"domain": ["switch", "input_boolean"]}}),
                    vol.Optional(
                        "heatPump",
                        description={"suggested_value": self.options.get("heatPump")},
                    ): selector(
                        {"entity": {"domain": ["switch", "input_boolean", "climate"]}}
                    ),
                    vol.Optional(
                        "heatPumpPower",
                        description={
                            "suggested_value": self.options.get("heatPumpPower")
                        },
                    ): selector({"entity": {"domain": "sensor", "device_class": "power"}}),
                }
            ),
            last_step=False,
        )

    async def async_step_filtration(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Handle the filtration step of the options flow."""

        if user_input is not None:
            user_input["distributionDatePivot"] = _validate_distribution(
                user_input.get("distributionDatePivot"), "distributionDatePivot", 1
            )
            self.options.update(user_input)
            return await self.async_step_init()

        schema = {
            vol.Optional(
                "methodeCalcul", default=str(self.options.get("methodeCalcul", 1))
            ): selector(
                {
                    "select": {
                        "mode": "dropdown",
                        "options": [
                            {"value": "1", "label": "Courbe de température"},
                            {"value": "2", "label": "Température / 2"},
                        ],
                    }
                }
            ),
            vol.Optional(
                "coefficientAjustement",
                default=self.options.get("coefficientAjustement", 1.0),
            ): selector(
                {
                    "number": {
                        "min": 0.3,
                        "max": 1.7,
                        "step": 0.1,
                        "mode": "slider",
                        "unit_of_measurement": "x",
                    }
                }
            ),
            vol.Optional(
                "datePivot", default=self.options.get("datePivot", "13:00")
            ): str,
            vol.Optional("pausePivot", default=self.options.get("pausePivot", 0)): int,
            vol.Optional(
                "distributionDatePivot",
                default=str(self.options.get("distributionDatePivot", 1)),
            ): selector(
                {
                    "select": {
                        "mode": "dropdown",
                        "options": [
                            {"value": "1", "label": "(1/2 <> 1/2)"},
                            {"value": "2", "label": "(1/3 <> 2/3)"},
                            {"value": "3", "label": "(2/3 <> 1/3)"},
                            {"value": "4", "label": "(1/1 <>)"},
                            {"value": "5", "label": "(<> 1/1)"},
                        ],
                    }
                }
            ),
            vol.Optional(
                "tempsDeFiltrationMinimum",
                default=self.options.get("tempsDeFiltrationMinimum", 3),
            ): int,
        }

        return self.async_show_form(
            step_id="filtration", data_schema=vol.Schema(schema), last_step=False
        )

    async def async_step_hivernage(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Handle the hivernage step of the options flow."""

        if user_input is not None:
            user_input["distributionDatePivotHivernage"] = _validate_distribution(
                user_input.get("distributionDatePivotHivernage"),
                "distributionDatePivotHivernage",
                4,
            )
            self.options.update(user_input)
            return await self.async_step_init()

        return self.async_show_form(
            step_id="hivernage",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "traitementHivernage",
                        default=self.options.get("traitementHivernage", False),
                    ): bool,
                    vol.Optional(
                        "coefficientAjustementHivernage",
                        default=self.options.get("coefficientAjustementHivernage", 1.0),
                    ): selector(
                        {
                            "number": {
                                "min": 0.3,
                                "max": 1.7,
                                "step": 0.1,
                                "mode": "slider",
                                "unit_of_measurement": "x",
                            }
                        }
                    ),
                    vol.Optional(
                        "distributionDatePivotHivernage",
                        default=str(
                            self.options.get("distributionDatePivotHivernage", 4)
                        ),
                    ): selector(
                        {
                            "select": {
                                "mode": "dropdown",
                                "options": [
                                    {"value": "1", "label": "(1/2 <> 1/2)"},
                                    {"value": "2", "label": "(1/3 <> 2/3)"},
                                    {"value": "3", "label": "(2/3 <> 1/3)"},
                                    {"value": "4", "label": "(1/1 <>)"},
                                    {"value": "5", "label": "(<> 1/1)"},
                                ],
                            }
                        }
                    ),
                    vol.Optional(
                        "choixHeureFiltrationHivernage",
                        default=self.options.get("choixHeureFiltrationHivernage", 1),
                    ): int,
                    vol.Optional(
                        "datePivotHivernage",
                        default=self.options.get("datePivotHivernage", "06:00"),
                    ): str,
                    vol.Optional(
                        "temperatureSecurite",
                        default=self.options.get("temperatureSecurite", -2),
                    ): int,
                    vol.Optional(
                        "temperatureHysteresis",
                        default=self.options.get("temperatureHysteresis", 0.5),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "filtration5mn3h",
                        default=self.options.get("filtration5mn3h", False),
                    ): bool,
                }
            ),
            last_step=False,
        )

    async def async_step_avance(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Handle the avance step of the options flow."""

        if user_input is not None:
            self.options.update(user_input)
            return await self.async_step_init()

        return self.async_show_form(
            step_id="avance",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "disableMarcheForcee",
                        default=self.options.get("disableMarcheForcee", False),
                    ): bool,
                    vol.Optional(
                        "sondeLocalTechnique",
                        default=self.options.get("sondeLocalTechnique", False),
                    ): bool,
                    vol.Optional(
                        "sondeLocalTechniquePause",
                        default=self.options.get("sondeLocalTechniquePause", 0),
                    ): int,
                    vol.Optional(
                        "surpresseurDuree",
                        default=self.options.get("surpresseurDuree", 5),
                    ): int,
                    vol.Optional(
                        "lavageDuree", default=self.options.get("lavageDuree", 2)
                    ): int,
                    vol.Optional(
                        "rincageDuree", default=self.options.get("rincageDuree", 2)
                    ): int,
                }
            ),
            last_step=False,
        )

    async def async_step_confirm(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Handle the confirm step of the options flow."""

        return self.async_create_entry(title="Pool Management", data=self.options)
