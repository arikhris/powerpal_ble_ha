"""BLE Client for PowerPal devices using Home Assistant's Bluetooth integration."""
from __future__ import annotations

import logging
from typing import Any, Callable

from bleak import BleakClient, BleakError
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class PowerPalBLEClient:
    """Manages BLE connections to PowerPal devices."""

    SERVICE_POWERPAL_UUID = "59DAABCD-12F4-25A6-7D4F-55961DCE4205"
    CHAR_MEASUREMENT_UUID = "59DA0001-12F4-25A6-7D4F-55961DCE4205"
    CHAR_PAIRINGCODE_UUID = "59DA0011-12F4-25A6-7D4F-55961DCE4205"

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        pairing_code: int,
        pulses_per_kwh: int = 1000,
    ):
        """Initialize the PowerPal BLE client."""
        self.hass = hass
        self.address = address
        self.pairing_code = pairing_code
        self.pulses_per_kwh = pulses_per_kwh
        self.client: BleakClient | None = None
        self._is_connected = False
        self._is_paired = False
        self._callbacks: list[Callable] = []

    async def connect(self) -> bool:
        """Connect to the PowerPal device."""
        try:
            ble_device = await async_ble_device_from_address(self.hass, self.address)
            if not ble_device:
                _LOGGER.error("Could not find PowerPal device at %s", self.address)
                return False

            self.client = BleakClient(ble_device)
            await self.client.connect()
            self._is_connected = True
            _LOGGER.info("Connected to PowerPal at %s", self.address)

            # Authenticate with pairing code
            if not await self._pair():
                await self.disconnect()
                return False

            # Start listening for notifications
            await self._start_notifications()

            self._notify_callbacks("connected")
            return True

        except BleakError as err:
            _LOGGER.error("Failed to connect to PowerPal: %s", err)
            return False

    async def disconnect(self) -> None:
        """Disconnect from the PowerPal device."""
        if self.client:
            try:
                await self.client.disconnect()
                self._is_connected = False
                _LOGGER.info("Disconnected from PowerPal")
                self._notify_callbacks("disconnected")
            except BleakError as err:
                _LOGGER.warning("Error disconnecting from PowerPal: %s", err)

    async def _pair(self) -> bool:
        """Authenticate with the PowerPal device using pairing code."""
        try:
            pairing_bytes = self._convert_pairing_code(self.pairing_code)
            await self.client.write_gatt_char(self.CHAR_PAIRINGCODE_UUID, pairing_bytes)
            self._is_paired = True
            _LOGGER.debug("Successfully authenticated with PowerPal")
            return True
        except BleakError as err:
            _LOGGER.error("Failed to authenticate with PowerPal: %s", err)
            return False

    async def _start_notifications(self) -> None:
        """Start listening for measurement notifications from PowerPal."""
        try:
            await self.client.start_notify(
                self.CHAR_MEASUREMENT_UUID, self._on_measurement_notification
            )
            _LOGGER.debug("Started listening for PowerPal notifications")
        except BleakError as err:
            _LOGGER.error("Failed to start notifications: %s", err)

    def _on_measurement_notification(self, sender: int, data: bytearray) -> None:
        """Handle incoming measurement notification from PowerPal."""
        measurement = self._parse_measurement_data(data)
        if measurement:
            self._notify_callbacks("measurement", measurement)

    def _parse_measurement_data(self, data: bytearray) -> dict[str, Any] | None:
        """Parse raw PowerPal measurement data.
        
        Data format:
        - Bytes 0-3: Unix timestamp (little-endian uint32)
        - Bytes 4-5: Pulse count (little-endian uint16)
        """
        if len(data) < 6:
            _LOGGER.warning("Invalid measurement data length: %d", len(data))
            return None

        try:
            unix_time = int.from_bytes(data[0:4], byteorder="little")
            pulse_count = int.from_bytes(data[4:6], byteorder="little")
            power_kw = pulse_count / self.pulses_per_kwh

            return {
                "timestamp": unix_time,
                "pulses": pulse_count,
                "power_kw": power_kw,
            }
        except (ValueError, IndexError) as err:
            _LOGGER.error("Error parsing measurement data: %s", err)
            return None

    @staticmethod
    def _convert_pairing_code(pairing_code: int) -> bytes:
        """Convert pairing code to PowerPal format (4-byte little-endian)."""
        return pairing_code.to_bytes(4, byteorder="little")

    def add_callback(self, callback: Callable) -> None:
        """Add a callback for connection state changes and measurements."""
        self._callbacks.append(callback)

    def _notify_callbacks(self, event_type: str, data: Any = None) -> None:
        """Notify all callbacks of an event."""
        for callback in self._callbacks:
            try:
                callback(event_type, data)
            except Exception as err:
                _LOGGER.error("Error in callback: %s", err)

    @property
    def is_connected(self) -> bool:
        """Return whether the client is connected."""
        return self._is_connected

    @property
    def is_paired(self) -> bool:
        """Return whether the client is paired."""
        return self._is_paired