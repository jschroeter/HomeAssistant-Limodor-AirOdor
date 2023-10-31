"""Constants for limodor_airodor."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "LIMODOR AirOdor"
DOMAIN = "limodor_airodor"
VERSION = "0.0.0"
ATTRIBUTION = ""
CONF_SERIAL_DEVICE = "Serial device"

BINARY_COMMAND_MAP = {
    "heat_recovery": [0x01, 0x02, 0x04],  # 40, 55 and 100% speed
    "summer_ventilation": [None, 0x08, 0x10],  # doesn't support 40%
    "only_air_in": [None, 0x20, 0x40],  # doesn't support 40%
}

PRESET_MODES = list(BINARY_COMMAND_MAP.keys())

SPEED_INDEX_PERCENTAGE = [40, 55, 100]


def binary_to_mode_and_percentage(binary_command):
    """Convert binary command to preset_mode and speed percentage."""
    if binary_command == 0x80:
        return {"preset_mode": PRESET_MODES[0], "percentage": 0}

    index = None
    preset_mode = None
    for current_preset_mode, speeds in BINARY_COMMAND_MAP.items():
        try:
            index = speeds.index(binary_command)
            preset_mode = current_preset_mode
            break
        except ValueError:
            pass

    if index is not None:
        return {"preset_mode": preset_mode, "percentage": SPEED_INDEX_PERCENTAGE[index]}


def mode_and_percentage_to_binary(mode, percentage):
    """Convert preset_mode and speed percentage to binary command."""
    if percentage == 0:
        return 0x80

    speed_index = SPEED_INDEX_PERCENTAGE.index(percentage)
    return BINARY_COMMAND_MAP[mode][speed_index]
