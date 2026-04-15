"""Sensor platform for PowerPal BLE."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_NAME,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .ble_client import PowerPalBLEClient
from . import (
    CONF_PAIRING_CODE,
    CONF_PULSES_PER_KWH,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors from a config entry."""
    address = entry.data[CONF_ADDRESS]
    name = entry.data.get(CONF_NAME, "PowerPal")
    pairing_code = entry.data[CONF_PAIRING_CODE]
    pulses_per_kwh = entry.data.get(CONF_PULSES_PER_KWH, 1000)

    ble_client = PowerPalBLEClient(hass, address, pairing_code, pulses_per_kwh)
    connected = await ble_client.connect()
    
    if not connected:
        _LOGGER.error("Failed to connect to PowerPal device")
        return

    hass.data[DOMAIN][entry.entry_id]["ble_client"] = ble_client
    entities = [PowerPalPowerSensor(ble_client, name, address)]
    async_add_entities(entities)


class PowerPalPowerSensor(SensorEntity):
    """Representation of a PowerPal power sensor."""

    def __init__(
        self,
        ble_client: PowerPalBLEClient,
        device_name: str,
        device_address: str,
    ) -> None:
        """Initialize the sensor."""
        self._ble_client = ble_client
        self._device_name = device_name
        self._device_address = device_address

        self._attr_name = f"{device_name} Power"
        self._attr_unique_id = f"{device_address}_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_value = 0.0

    async def async_added_to_hass(self) -> None:
        """Handle entity addition."""
        self._ble_client.add_callback(self._on_ble_event)

    @callback
    def _on_ble_event(self, event_type: str, data: Any = None) -> None:
        """Handle BLE events."""
        if event_type == "measurement" and data:
            self._attr_native_value = data["power_kw"]
            self.async_write_ha_state()
        elif event_type == "connected":
            self.async_write_ha_state()
        elif event_type == "disconnected":
            self._attr_native_value = None
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return whether the sensor is available."""
        return self._ble_client.is_connected and self._ble_client.is_paired