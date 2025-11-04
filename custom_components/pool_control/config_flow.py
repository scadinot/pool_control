"""Config flow for Pool Control integration."""

from typing import Any, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, FlowResult
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import DOMAIN
from .options_flow import PoolControlOptionsFlowHandler


class PoolControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestion de la configuration initiale de Pool Control via l'UI."""

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Étape initiale de configuration."""
        if user_input is not None:
            return self.async_create_entry(title="Pool Control", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("temperatureWater"): selector(
                        {"entity": {"domain": ["sensor", "input_number"]}}
                    ),
                    vol.Required("temperatureOutdoor"): selector(
                        {"entity": {"domain": ["sensor", "input_number"]}}
                    ),
                    vol.Required("leverSoleil"): selector(
                        {"entity": {"domain": ["sensor", "input_number"]}}
                    ),
                    vol.Required("filtration"): selector(
                        {"entity": {"domain": ["switch", "input_boolean"]}}
                    ),
                    vol.Required("traitement"): selector(
                        {"entity": {"domain": ["switch", "input_boolean"]}}
                    ),
                    vol.Optional("traitement_2"): selector(
                        {"entity": {"domain": ["switch", "input_boolean"]}}
                    ),
                    vol.Required("surpresseur"): selector(
                        {"entity": {"domain": ["switch", "input_boolean"]}}
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> PoolControlOptionsFlowHandler:
        """Retourne le flow d'options amélioré."""

        return PoolControlOptionsFlowHandler(config_entry)
