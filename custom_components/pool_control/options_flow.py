"""Options flow for Pool Control integration."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import selector


class PoolControlOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestion des options de Pool Control avec menu de navigation."""

    def __init__(self, config_entry):
        """Initialize the options flow."""

        self.config_entry = config_entry
        self.options = {**config_entry.data, **config_entry.options}

    async def async_step_init(self, user_input=None):
        """Étape initiale de configuration des options."""

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

    async def async_step_user(self, user_input=None):
        """Handle the user step of the options flow."""

        if user_input is not None:
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
                    vol.Optional(
                        "traitement_2", default=self.options.get("traitement_2")
                    ): selector({"entity": {"domain": ["switch", "input_boolean"]}}),
                    vol.Required(
                        "surpresseur", default=self.options.get("surpresseur")
                    ): selector({"entity": {"domain": ["switch", "input_boolean"]}}),
                }
            ),
            last_step=False,
        )

    async def async_step_filtration(self, user_input=None):
        """Handle the filtration step of the options flow."""

        if user_input is not None:
            user_input["distributionDatePivot"] = int(
                user_input.get("distributionDatePivot")
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

    async def async_step_hivernage(self, user_input=None):
        """Handle the hivernage step of the options flow."""

        if user_input is not None:
            user_input["distributionDatePivotHivernage"] = int(
                user_input.get("distributionDatePivotHivernage")
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

    async def async_step_avance(self, user_input=None):
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

    async def async_step_confirm(self, user_input=None):
        """Handle the confirm step of the options flow."""

        return self.async_create_entry(title="Pool Control", data=self.options)
