"""Platform for fan integration."""
from __future__ import annotations

import hashlib
from time import monotonic, sleep
from typing import Any

import serialx
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_SERIAL_DEVICE,
    LOGGER,
    PRESET_MODES,
    binary_to_mode_and_percentage,
    mode_and_percentage_to_binary,
)

ORDERED_NAMED_FAN_SPEEDS = ["quiet", "normal", "max"]  # off is not included
SERIAL_RESPONSE_INDEX = 4
# STATUS returns 9 bytes (fan off) or 11 bytes (fan on); read the minimum reliable length.
SERIAL_RESPONSE_LENGTH_STATUS = 9
# SET commands are echoed back as exactly 7 bytes.
SERIAL_RESPONSE_LENGTH_SET = 7
# Give the device a brief moment before starting reads after a write.
SERIAL_POST_WRITE_DELAY_SECONDS = 0.05
# Total time budget for collecting a full response frame.
SERIAL_READ_DEADLINE_SECONDS = 3.0
STATUS_COMMAND = bytearray([0x02, 0x02, 0x96, 0x96])


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Platform setup."""
    async_add_entities([AirOdorFan("/dev/ttyUSB0")])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry setup."""
    serial_device = config_entry.data[CONF_SERIAL_DEVICE]
    async_add_entities([AirOdorFan(serial_device)])


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

    def _open_serial_connection(self):
        """Create the serial connection for the device."""
        return serialx.serial_for_url(
            self._serial_device,
            baudrate=9600,
            byte_size=8,
            parity=serialx.Parity.NONE,
            stopbits=serialx.StopBits.ONE,
            read_timeout=1,
        )

    def _send_command(
        self,
        values: bytearray,
        operation: str,
        response_length: int = SERIAL_RESPONSE_LENGTH_STATUS,
    ) -> bytes | None:
        """Send a command to the device and return the raw response."""
        try:
            with self._open_serial_connection() as ser:
                ser.readall()  # flush any stale bytes before sending
                ser.write(values)
                sleep(SERIAL_POST_WRITE_DELAY_SECONDS)

                response = bytearray()
                deadline = monotonic() + SERIAL_READ_DEADLINE_SECONDS
                while len(response) < response_length and monotonic() < deadline:
                    chunk = ser.read(response_length - len(response))
                    if not chunk:
                        continue
                    response.extend(chunk)

                if len(response) < response_length:
                    LOGGER.debug(
                        "AirOdorFan %s short response after retries (%d/%d bytes)",
                        operation,
                        len(response),
                        response_length,
                    )
        except (OSError, serialx.SerialException) as err:
            self._attr_available = False
            LOGGER.warning(
                "AirOdorFan %s failed. Serial communication error: %s",
                operation,
                err,
            )
            return None

        return bytes(response)

    def _has_valid_response(
        self,
        response: bytes | None,
        operation: str,
        expected_length: int,
    ) -> bool:
        """Validate the response returned by the device."""
        if response is None:
            LOGGER.warning(
                "AirOdorFan %s failed. Device response is missing.",
                operation,
            )
            return False

        if len(response) < expected_length:
            LOGGER.warning(
                "AirOdorFan %s failed. Incomplete device frame (%d/%d bytes): %s",
                operation,
                len(response),
                expected_length,
                response,
            )
            return False

        if len(response) <= SERIAL_RESPONSE_INDEX:
            LOGGER.warning(
                "AirOdorFan %s failed. Device response too short for command index: %s",
                operation,
                response,
            )
            return False

        return True

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

    @staticmethod
    def _build_set_command(binary_command: int) -> bytearray:
        """Build the command used to set fan speed and mode."""
        return bytearray([0x02, 0x05, 0x16, 0x00, binary_command, binary_command, 0x11])

    def send_serial_command(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
    ) -> bool:
        """Set the speed of the fan, as a percentage."""
        if percentage is None:
            percentage = self._percentage
        if preset_mode is None:
            preset_mode = self._preset_mode
        if percentage is None:
            LOGGER.warning(
                "AirOdorFan send_serial_command failed. Missing fan percentage."
            )
            return False

        binary_command = mode_and_percentage_to_binary(preset_mode, percentage)
        response = self._send_command(
            self._build_set_command(binary_command),
            "send_serial_command",
            SERIAL_RESPONSE_LENGTH_SET,
        )

        if not self._has_valid_response(
            response,
            "send_serial_command",
            SERIAL_RESPONSE_LENGTH_SET,
        ):
            return False

        response_command = response[SERIAL_RESPONSE_INDEX]
        if response_command != binary_command:
            self._attr_available = False
            LOGGER.warning(
                "AirOdorFan send_serial_command failed. Got %s, expected %s",
                response_command,
                binary_command,
            )
            return False

        self._attr_available = True
        LOGGER.debug(
            "AirOdorFan send_serial_command decoded write: command=0x%02X preset_mode=%s percentage=%s response_len=%d",
            binary_command,
            preset_mode,
            percentage,
            len(response),
        )
        LOGGER.info("AirOdorFan send_serial_command successful")
        return True

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
        response = self._send_command(STATUS_COMMAND, "update")
        if not self._has_valid_response(response, "update", SERIAL_RESPONSE_LENGTH_STATUS):
            return False

        response_command = response[SERIAL_RESPONSE_INDEX]
        mode_and_percentage = binary_to_mode_and_percentage(response_command)
        if mode_and_percentage is None:
            self._attr_available = False
            LOGGER.warning(
                "AirOdorFan update failed. Unknown device response command: %s",
                response_command,
            )
            return False

        LOGGER.debug(
            "AirOdorFan update decoded state: command=0x%02X preset_mode=%s percentage=%s",
            response_command,
            mode_and_percentage["preset_mode"],
            mode_and_percentage["percentage"],
        )
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
        if self.send_serial_command(value, self._preset_mode):
            # Optimistically apply written state so UI updates immediately.
            self._percentage = value
            # Read back from the device; keep optimistic state if readback fails.
            self._update_from_device()
            self.schedule_update_ha_state()
            return

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

            if self.send_serial_command(self._percentage, preset_mode):
                # Optimistically apply written state so UI updates immediately.
                self._preset_mode = preset_mode
                # Read back from the device; keep optimistic state if readback fails.
                self._update_from_device()
                self.schedule_update_ha_state()
                return

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
