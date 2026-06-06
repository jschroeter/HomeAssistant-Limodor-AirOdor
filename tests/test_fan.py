"""Unit tests for fan entity behavior with mocked serial client."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

pytest.importorskip("homeassistant")

from custom_components.limodor_airodor.fan import AirOdorFan  # noqa: E402


def test_update_from_device_applies_client_state() -> None:
    """Entity should adopt decoded state from client reads."""
    fan = AirOdorFan("loop://")
    fan._client.read_state = Mock(  # noqa: SLF001
        return_value={"preset_mode": "heat_recovery", "percentage": 55}
    )

    result = fan._update_from_device()  # noqa: SLF001

    assert result is True
    assert fan.percentage == 55
    assert fan.preset_mode == "heat_recovery"
    assert fan.available is True


def test_set_percentage_normalizes_and_writes() -> None:
    """Entity should normalize HA percentage before sending to device."""
    fan = AirOdorFan("loop://")
    fan.schedule_update_ha_state = Mock()
    fan._preset_mode = "heat_recovery"  # noqa: SLF001
    fan._client.send_serial_command = Mock(return_value=True)  # noqa: SLF001

    fan.set_percentage(41)

    fan._client.send_serial_command.assert_called_once_with(55, "heat_recovery")  # noqa: SLF001
    assert fan.percentage == 55


def test_set_preset_mode_while_off_updates_only_local_state() -> None:
    """Changing preset while off should not issue serial command immediately."""
    fan = AirOdorFan("loop://")
    fan.schedule_update_ha_state = Mock()
    fan._percentage = 0  # noqa: SLF001
    fan._client.send_serial_command = Mock(return_value=True)  # noqa: SLF001

    fan.set_preset_mode("summer_bypass")

    fan._client.send_serial_command.assert_not_called()  # noqa: SLF001
    assert fan.preset_mode == "summer_bypass"


def test_set_preset_mode_when_running_writes_to_device() -> None:
    """Changing preset while running should call serial write path."""
    fan = AirOdorFan("loop://")
    fan.schedule_update_ha_state = Mock()
    fan._percentage = 55  # noqa: SLF001
    fan._client.send_serial_command = Mock(return_value=True)  # noqa: SLF001

    fan.set_preset_mode("only_air_in")

    fan._client.send_serial_command.assert_called_once_with(55, "only_air_in")  # noqa: SLF001
    assert fan.preset_mode == "only_air_in"
