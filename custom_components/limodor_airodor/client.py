# Copyright (c) 2024 jschroeter
"""Serial client for LIMODOR AirOdor device communication."""
from __future__ import annotations

from time import monotonic, sleep

import serialx

from .const import (
    LOGGER,
    SERIAL_POST_WRITE_DELAY_SECONDS,
    SERIAL_READ_DEADLINE_SECONDS,
    SERIAL_RESPONSE_INDEX,
    SERIAL_RESPONSE_LENGTH_SET,
    SERIAL_RESPONSE_LENGTH_STATUS,
    STATUS_COMMAND,
    binary_to_mode_and_percentage,
    mode_and_percentage_to_binary,
)


class AirOdorClient:
    """Client that encapsulates serial transport and protocol parsing."""

    def __init__(self, serial_device: str) -> None:
        """Initialize the client for a specific serial device path."""
        self._serial_device = serial_device

    def _open_serial_connection(self) -> serialx.Serial:
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
                        "AirOdorClient %s short response after retries (%d/%d bytes)",
                        operation,
                        len(response),
                        response_length,
                    )
        except (OSError, serialx.SerialException) as err:
            LOGGER.warning(
                "AirOdorClient %s failed. Serial communication error: %s",
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
                "AirOdorClient %s failed. Device response is missing.",
                operation,
            )
            return False

        if len(response) < expected_length:
            LOGGER.warning(
                "AirOdorClient %s failed. Incomplete device frame (%d/%d bytes): %s",
                operation,
                len(response),
                expected_length,
                response,
            )
            return False

        if len(response) <= SERIAL_RESPONSE_INDEX:
            LOGGER.warning(
                (
                    "AirOdorClient %s failed. "
                    "Device response too short for command index: %s"
                ),
                operation,
                response,
            )
            return False

        return True

    @staticmethod
    def _build_set_command(binary_command: int) -> bytearray:
        """Build the command used to set fan speed and mode."""
        return bytearray([0x02, 0x05, 0x16, 0x00, binary_command, binary_command, 0x11])

    def send_serial_command(
        self,
        percentage: int | None,
        preset_mode: str,
    ) -> bool:
        """Set fan speed/preset and validate echoed response."""
        if percentage is None:
            LOGGER.warning(
                "AirOdorClient send_serial_command failed. Missing fan percentage."
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
            LOGGER.warning(
                "AirOdorClient send_serial_command failed. Got %s, expected %s",
                response_command,
                binary_command,
            )
            return False

        LOGGER.debug(
            (
                "AirOdorClient send_serial_command decoded write: "
                "command=0x%02X preset_mode=%s percentage=%s response_len=%d"
            ),
            binary_command,
            preset_mode,
            percentage,
            len(response),
        )
        LOGGER.info("AirOdorClient send_serial_command successful")
        return True

    def read_state(self) -> dict[str, str | int] | None:
        """Read and decode the current device state."""
        response = self._send_command(STATUS_COMMAND, "update")
        if not self._has_valid_response(
            response,
            "update",
            SERIAL_RESPONSE_LENGTH_STATUS,
        ):
            return None

        response_command = response[SERIAL_RESPONSE_INDEX]
        mode_and_percentage = binary_to_mode_and_percentage(response_command)
        if mode_and_percentage is None:
            LOGGER.warning(
                "AirOdorClient update failed. Unknown device response command: %s",
                response_command,
            )
            return None

        LOGGER.debug(
            (
                "AirOdorClient update decoded state: "
                "command=0x%02X preset_mode=%s percentage=%s"
            ),
            response_command,
            mode_and_percentage["preset_mode"],
            mode_and_percentage["percentage"],
        )
        return mode_and_percentage
