"""Inter-MCU Framing Protocol and Checksum Utilities (Arduino Nano <-> ESP32)."""

from typing import Tuple, Optional


class GateProtocolOpcodes:
    # Downstream Commands (ESP32 -> Nano)
    CMD_TOGGLE_CYCLE    = 0x10
    CMD_PEDESTRIAN_OPEN = 0x11
    CMD_EMERGENCY_HALT  = 0x12
    CMD_SET_ECO_MODE    = 0x13

    # Upstream Telemetry (Nano -> ESP32)
    TEL_LIVE_TELEMETRY  = 0x20
    TEL_SAFETY_ALERT    = 0x30
    TEL_ACK             = 0x06


START_BYTE = 0x02
STOP_BYTE  = 0x03


def calculate_crc8(data: bytes) -> int:
    """Computes CRC-8 checksum with polynomial 0x07 (standard Dallas/Maxim)."""
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def build_frame(opcode: int, payload: bytes = b"") -> bytes:
    """Encapsulates an opcode and payload into a validated UART transmission frame."""
    length = len(payload)
    header_and_payload = bytes([opcode, length]) + payload
    crc = calculate_crc8(header_and_payload)
    return bytes([START_BYTE]) + header_and_payload + bytes([crc, STOP_BYTE])


def parse_frame(frame: bytes) -> Optional[Tuple[int, bytes]]:
    """Validates frame framing and CRC-8. Returns (opcode, payload) on success."""
    if len(frame) < 5:
        return None
    if frame[0] != START_BYTE or frame[-1] != STOP_BYTE:
        return None

    header_and_payload = frame[1:-2]
    expected_crc = frame[-2]

    if calculate_crc8(header_and_payload) != expected_crc:
        return None

    opcode = header_and_payload[0]
    payload = header_and_payload[2:]
    return opcode, payload
