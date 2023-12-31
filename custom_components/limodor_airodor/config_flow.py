"""Adds config flow for limodor_airodor."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_SERIAL_DEVICE


class LimodorAirOdorFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for limodor_airodor."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_SERIAL_DEVICE],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERIAL_DEVICE,
                        default="/dev/ttyUSB0",
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=_errors,
        )
