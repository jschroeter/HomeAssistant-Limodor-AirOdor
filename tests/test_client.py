"""Unit tests for serial client behavior."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
import serialx

pytest.importorskip("homeassistant")

from custom_components.limodor_airodor.client import AirOdorClient  # noqa: E402


@dataclass
class FakeSerial:
    """Simple serial port stub for deterministic protocol tests."""

    reads: list[bytes]
    written: list[bytes] = field(default_factory=list)

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit context manager."""
        return False

    def readall(self) -> bytes:
        """Return no buffered bytes."""
        return b""

    def write(self, values: bytes) -> int:
        """Capture write payload."""
        self.written.append(bytes(values))
        return len(values)

    def read(self, _size: int) -> bytes:
        """Return next queued chunk or empty bytes."""
        if not self.reads:
            return b""
        return self.reads.pop(0)


def test_send_serial_command_success() -> None:
    """Write command succeeds when echo matches expected command byte."""
    fake_serial = FakeSerial(reads=[b"\x02\x05\x16\x00\x02\x02\x11"])
    client = AirOdorClient("loop://")
    client._open_serial_connection = lambda: fake_serial  # noqa: SLF001

    assert client.send_serial_command(55, "heat_recovery") is True
    assert fake_serial.written


def test_send_serial_command_fails_on_echo_mismatch() -> None:
    """Write command fails when response echo differs from requested command."""
    fake_serial = FakeSerial(reads=[b"\x02\x05\x16\x00\x04\x04\x11"])
    client = AirOdorClient("loop://")
    client._open_serial_connection = lambda: fake_serial  # noqa: SLF001

    assert client.send_serial_command(55, "heat_recovery") is False


def test_send_serial_command_fails_on_serial_exception() -> None:
    """Write command fails gracefully if opening serial connection errors."""

    def raise_error():
        raise serialx.SerialException("boom")

    client = AirOdorClient("loop://")
    client._open_serial_connection = raise_error  # noqa: SLF001

    assert client.send_serial_command(55, "heat_recovery") is False


def test_read_state_success() -> None:
    """Read state decodes valid command byte into preset and percentage."""
    fake_serial = FakeSerial(reads=[b"\x02\x02\x96\x96\x04\x00\x00\x00\x00"])
    client = AirOdorClient("loop://")
    client._open_serial_connection = lambda: fake_serial  # noqa: SLF001

    state = client.read_state()

    assert state == {"preset_mode": "heat_recovery", "percentage": 100}


def test_read_state_fails_on_unknown_command() -> None:
    """Read state returns None for unsupported command bytes."""
    fake_serial = FakeSerial(reads=[b"\x02\x02\x96\x96\x7F\x00\x00\x00\x00"])
    client = AirOdorClient("loop://")
    client._open_serial_connection = lambda: fake_serial  # noqa: SLF001

    assert client.read_state() is None


def test_read_state_fails_on_short_frame() -> None:
    """Read state returns None when status frame is incomplete."""
    fake_serial = FakeSerial(reads=[b"\x02\x02\x96\x96\x04"])
    client = AirOdorClient("loop://")
    client._open_serial_connection = lambda: fake_serial  # noqa: SLF001

    assert client.read_state() is None
