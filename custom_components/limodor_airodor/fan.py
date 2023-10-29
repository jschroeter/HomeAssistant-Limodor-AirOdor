"""Platform for light integration."""
from __future__ import annotations

import serial

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    LOGGER,
    PRESET_MODES,
    binary_to_mode_and_percentage,
    mode_and_percentage_to_binary,
)

ORDERED_NAMED_FAN_SPEEDS = ["quiet", "normal", "max"]  # off is not included


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Platform setup."""
    async_add_entities([AirOdorFan()])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry setup."""
    await async_setup_platform(hass, {}, async_add_entities)


class AirOdorFan(FanEntity):
    """AirOdor entity based on the FanEntity."""

    @property
    def unique_id(self) -> str:
        """Return the unique id."""
        return self._unique_id

    @property
    def percentage(self) -> Optional[int]:
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

    def __init__(self) -> None:
        """Init the AirOdorFan."""
        self._unique_id = "fan"
        self._attr_name = "LIMODOR AirOdor"
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE
        )
        self._percentage: int | None = None
        self._current_named_speed: str | None = None
        self._preset_modes = PRESET_MODES
        self._preset_mode = PRESET_MODES[0]

    def send_serial_command(self) -> None:
        """Set the speed of the fan, as a percentage."""

        percentage = self._percentage
        preset_mode = self._preset_mode

        # LOGGER.info("AirOdorFan send_serial_command" + str(percentage) + preset_mode)

        binary_command = mode_and_percentage_to_binary(preset_mode, percentage)

        ser = serial.Serial(
            "/dev/ttyUSB0",
            9600,
            serial.EIGHTBITS,
            serial.PARITY_NONE,
            serial.STOPBITS_ONE,
            1,
        )
        values = bytearray(
            [0x02, 0x05, 0x16, 0x00, binary_command, binary_command, 0x11]
        )
        ser.write(values)
        response = ser.read(11)
        ser.close()

        response_command = response[4]
        if response_command != binary_command:
            LOGGER.warning(
                "AirOdorFan send_serial_command failed. Got "
                + response_command
                + ", expected "
                + binary_command
            )
        else:
            LOGGER.info("AirOdorFan send_serial_command successful")

    def update(self) -> None:
        """Poll current state of the device and updates HA state."""
        ser = serial.Serial(
            "/dev/ttyUSB0",
            9600,
            serial.EIGHTBITS,
            serial.PARITY_NONE,
            serial.STOPBITS_ONE,
            1,
        )
        values = bytearray([0x02, 0x02, 0x96, 0x96])
        ser.write(values)
        response = ser.read(11)
        ser.close()

        if response is not None:
            mode_and_percentage = binary_to_mode_and_percentage(response[4])
            self._percentage = mode_and_percentage["percentage"]
            self._preset_mode = mode_and_percentage["preset_mode"]
            self.schedule_update_ha_state()

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage. AirOdor only supports 40, 55 and 100%."""
        if percentage <= 0:
            value = 0
        elif percentage <= 40:
            value = 40  # 12
        elif percentage <= 66:
            value = 55  # 15
        else:
            value = 100  # 28

        self._percentage = value
        self.schedule_update_ha_state()
        self.send_serial_command()

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
            self._preset_mode = preset_mode
            self.schedule_update_ha_state()
            self.send_serial_command()
        else:
            raise ValueError(f"Invalid preset mode: {preset_mode}")

    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""

        if percentage is None:
            percentage = 55

        self.set_percentage(percentage)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        self.set_percentage(0)
