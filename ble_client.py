"""The PowerPal BLE integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "powerpal_ble"

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# PowerPal Configuration
CONF_PAIRING_CODE = "pairing_code"
CONF_PULSES_PER_KWH = "pulses_per_kwh"

# Service UUIDs
SERVICE_POWERPAL_UUID = "59DAABCD-12F4-25A6-7D4F-55961DCE4205"

# Characteristic UUIDs
CHAR_MEASUREMENT_UUID = "59DA0001-12F4-25A6-7D4F-55961DCE4205"
CHAR_PAIRINGCODE_UUID = "59DA0011-12F4-25A6-7D4F-55961DCE4205"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PowerPal BLE integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PowerPal BLE from a config entry."""
    hass.data[DOMAIN][entry.entry_id] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class PowerPalBLEConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for PowerPal BLE."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ADDRESS])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, user_input[CONF_ADDRESS]),
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=cv.Schema(
                {
                    cv.Required(CONF_ADDRESS): cv.string,
                    cv.Optional(CONF_NAME, default="PowerPal"): cv.string,
                    cv.Required(CONF_PAIRING_CODE): cv.positive_int,
                    cv.Optional(CONF_PULSES_PER_KWH, default=1000): cv.positive_int,
                }
            ),
            errors={},
        )

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> Any:
        """Handle a flow initialized by Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        return self.async_show_form(
            step_id="user",
            data_schema=cv.Schema(
                {
                    cv.Required(CONF_ADDRESS, default=discovery_info.address): cv.string,
                    cv.Optional(CONF_NAME, default=discovery_info.name or "PowerPal"): cv.string,
                    cv.Required(CONF_PAIRING_CODE): cv.positive_int,
                    cv.Optional(CONF_PULSES_PER_KWH, default=1000): cv.positive_int,
                }
            ),
        )