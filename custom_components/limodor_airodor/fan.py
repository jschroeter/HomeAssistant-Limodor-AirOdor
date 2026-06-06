"""Platform for fan integration."""
from __future__ import annotations

import hashlib
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .client import AirOdorClient
from .const import (
    CONF_SERIAL_DEVICE,
    LOGGER,
    ORDERED_NAMED_FAN_SPEEDS,
    PRESET_MODES,
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """YAML platform setup is not supported; use config flow entries."""
    LOGGER.warning(
        "LIMODOR AirOdor YAML setup is unsupported. Configure via integration UI."
    )
    return


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry setup."""
    serial_device = config_entry.data[CONF_SERIAL_DEVICE]
    async_add_entities([AirOdorFan(serial_device)], update_before_add=True)


class AirOdorFan(FanEntity):
    """AirOdor entity based on the FanEntity."""

    _attr_available = True

    @property
    def unique_id(self) -> str:
        """Return the unique id."""
        return self._unique_id

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        return self._percentage

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(ORDERED_NAMED_FAN_SPEEDS)

    @property
    def is_on(self) -> bool | None:
        """Return true if the entity is on."""
        return self._percentage is not None and self._percentage > 0

    def __init__(self, serial_device: str) -> None:
        """Init the AirOdorFan."""
        self._serial_device = serial_device
        self._client = AirOdorClient(serial_device)
        device_hash = hashlib.sha1(serial_device.encode("utf-8")).hexdigest()[:12]
        self._unique_id = f"fan_{device_hash}"
        self._attr_name = "LIMODOR AirOdor"
        self._attr_translation_key = "limodor_airodor"
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
        )
        self._percentage: int | None = None
        self._current_named_speed: str | None = None
        self._preset_modes = PRESET_MODES
        self._preset_mode = PRESET_MODES[0]

    @staticmethod
    def _normalize_percentage(percentage: int) -> int:
        """Map Home Assistant percentages to supported device percentages."""
        if percentage <= 0:
            return 0
        if percentage <= 40:
            return 40
        if percentage <= 66:
            return 55
        return 100

    def _refresh_state_after_failed_command(self, operation: str) -> None:
        """Refresh the entity state after a failed write command."""
        LOGGER.info(
            "AirOdorFan %s failed. Refreshing state from device.",
            operation,
        )
        self.update()
        self.schedule_update_ha_state()

    def _update_from_device(self) -> bool:
        """Read and apply the current device state. Returns True on success."""
        mode_and_percentage = self._client.read_state()
        if mode_and_percentage is None:
            self._attr_available = False
            return False

        self._percentage = mode_and_percentage["percentage"]
        self._preset_mode = mode_and_percentage["preset_mode"]
        self._attr_available = True
        return True

    def update(self) -> None:
        """Poll current state of the device and updates HA state."""
        self._update_from_device()

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage. AirOdor only supports 40, 55 and 100%."""
        value = self._normalize_percentage(percentage)
        if self._client.send_serial_command(value, self._preset_mode):
            self._attr_available = True
            # Apply confirmed written state so UI updates immediately.
            self._percentage = value
            self.schedule_update_ha_state()
            return

        self._attr_available = False
        self._refresh_state_after_failed_command("set_percentage")

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode, e.g., auto, smart, interval, favorite."""
        return self._preset_mode

    @property
    def preset_modes(self) -> list[str] | None:
        """Return a list of available preset modes."""
        return self._preset_modes

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if self.preset_modes and preset_mode in self.preset_modes:
            if self._percentage is None or self._percentage == 0:
                LOGGER.info(
                    "AirOdorFan set_preset_mode while off. Preset will apply on the next speed change."
                )
                self._preset_mode = preset_mode
                self.schedule_update_ha_state()
                return

            if self._client.send_serial_command(self._percentage, preset_mode):
                self._attr_available = True
                # Apply confirmed written state so UI updates immediately.
                self._preset_mode = preset_mode
                self.schedule_update_ha_state()
                return

            self._attr_available = False
            self._refresh_state_after_failed_command("set_preset_mode")
        else:
            raise ValueError(f"Invalid preset mode: {preset_mode}")

    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""

        if percentage is None:
            percentage = 55

        self.set_percentage(percentage)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        self.set_percentage(0)
