"""Interactive test script for the AirOdor serial device."""
import time
import serialx

DEVICE = "/dev/cu.usbserial-AR0K4K2N"
SERIAL_RESPONSE_INDEX = 4
SERIAL_RESPONSE_LENGTH = 11
STATUS_COMMAND = bytearray([0x02, 0x02, 0x96, 0x96])

BINARY_COMMAND_MAP = {
    "heat_recovery": [0x01, 0x02, 0x04],  # 40, 55 and 100% speed
    "summer_bypass":  [None, 0x08, 0x10],
    "only_air_in":    [None, 0x20, 0x40],
}
SPEED_INDEX_PERCENTAGE = [40, 55, 100]
PRESET_MODES = list(BINARY_COMMAND_MAP.keys())


def binary_to_mode_and_percentage(binary_command):
    if binary_command == 0x80:
        return {"preset_mode": PRESET_MODES[0], "percentage": 0}
    for mode, speeds in BINARY_COMMAND_MAP.items():
        try:
            index = speeds.index(binary_command)
            return {"preset_mode": mode, "percentage": SPEED_INDEX_PERCENTAGE[index]}
        except ValueError:
            pass
    return None


def mode_and_percentage_to_binary(mode, percentage):
    if percentage == 0:
        return 0x80
    speed_index = SPEED_INDEX_PERCENTAGE.index(percentage)
    return BINARY_COMMAND_MAP[mode][speed_index]


def open_serial():
    return serialx.serial_for_url(
        DEVICE,
        baudrate=9600,
        byte_size=8,
        parity=serialx.Parity.NONE,
        stopbits=serialx.StopBits.ONE,
        read_timeout=2,
    )


def dump_response(label, response):
    if response is None:
        print(f"  [{label}] No response")
        return
    hex_str = " ".join(f"{b:02X}" for b in response)
    print(f"  [{label}] raw ({len(response)} bytes): {hex_str}")
    if len(response) > SERIAL_RESPONSE_INDEX:
        byte = response[SERIAL_RESPONSE_INDEX]
        decoded = binary_to_mode_and_percentage(byte)
        print(f"  [{label}] byte[{SERIAL_RESPONSE_INDEX}] = 0x{byte:02X}  → {decoded}")
    else:
        print(f"  [{label}] Response too short to decode")


def send_and_receive(label, command):
    hex_cmd = " ".join(f"{b:02X}" for b in command)
    print(f"\n→ Sending {label}: {hex_cmd}")
    try:
        with open_serial() as ser:
            ser.write(command)
            response = ser.read(SERIAL_RESPONSE_LENGTH)
    except (OSError, serialx.SerialException) as e:
        print(f"  ERROR: {e}")
        return None
    dump_response(label, response)
    return response


# ─── 1. STATUS query ───────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: STATUS query")
send_and_receive("STATUS", STATUS_COMMAND)
time.sleep(0.5)

# ─── 2. Set heat_recovery @ 55% ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: SET heat_recovery @ 55%")
bc = mode_and_percentage_to_binary("heat_recovery", 55)
set_cmd = bytearray([0x02, 0x05, 0x16, 0x00, bc, bc, 0x11])
send_and_receive(f"SET heat_recovery/55% (0x{bc:02X})", set_cmd)
time.sleep(1.0)

# ─── 3. STATUS query after SET ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: STATUS query (should reflect new speed/mode)")
send_and_receive("STATUS", STATUS_COMMAND)
time.sleep(0.5)

# ─── 4. Set heat_recovery @ 100% ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: SET heat_recovery @ 100%")
bc = mode_and_percentage_to_binary("heat_recovery", 100)
set_cmd = bytearray([0x02, 0x05, 0x16, 0x00, bc, bc, 0x11])
send_and_receive(f"SET heat_recovery/100% (0x{bc:02X})", set_cmd)
time.sleep(1.0)

# ─── 5. STATUS query after SET ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: STATUS query (should reflect 100%)")
send_and_receive("STATUS", STATUS_COMMAND)
time.sleep(0.5)

# ─── 6. Turn OFF (0x80) ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6: TURN OFF (0x80)")
bc = 0x80
set_cmd = bytearray([0x02, 0x05, 0x16, 0x00, bc, bc, 0x11])
send_and_receive(f"SET off (0x{bc:02X})", set_cmd)
time.sleep(1.0)

# ─── 7. Final STATUS ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 7: Final STATUS query (should report off)")
send_and_receive("STATUS", STATUS_COMMAND)

print("\nDone.")
