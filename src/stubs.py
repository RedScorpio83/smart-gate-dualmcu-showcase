"""Encapsulated Service Stubs and Specification Implementations for SmartGate.

Note: Proprietary PID motor acceleration curves, calibrated current trip points,
and physical installation secrets are encapsulated in production firmware.
These stubs demonstrate architectural contracts, safety state transitions, and failovers.
"""

from datetime import datetime
from typing import Optional
from .interfaces import (
    IRealTimeMotorController,
    ISafetySupervisor,
    IIoTSerialBridge,
    IHomeAssistantMqttPublisher,
)
from .models import (
    GateTelemetrySnapshot,
    GateMotionState,
    LeafTelemetry,
    AlarmCause,
    GateCommand,
)
from .serial_protocol import build_frame, parse_frame, GateProtocolOpcodes


class DualBts7960MotorControllerStub(IRealTimeMotorController):
    """Encapsulated driver stub for 2x BTS7960 H-Bridge controllers."""

    def __init__(self):
        self._currents = {1: 0.0, 2: 0.0}
        self._pwms = {1: 0, 2: 0}

    def set_motor_speed(self, leaf_id: int, direction: str, pwm_duty: int) -> None:
        self._pwms[leaf_id] = pwm_duty
        # In production, sets RPWM/LPWM timers via ATmega328 Hardware PWM registers

    def emergency_brake_all(self) -> None:
        self._pwms[1] = 0
        self._pwms[2] = 0
        # In production, writes both RPWM and LPWM HIGH simultaneously to activate dynamic braking

    def read_motor_current(self, leaf_id: int) -> float:
        return self._currents.get(leaf_id, 0.0)

    def simulate_load_current(self, leaf_id: int, amps: float) -> None:
        self._currents[leaf_id] = amps


class SafetySupervisorStub(ISafetySupervisor):
    """Deterministic real-time safety loop executing on Arduino Nano (< 2ms response)."""

    def __init__(self, current_threshold_amps: float = 5.5):
        self.threshold = current_threshold_amps
        self._photocell_blocked = False

    def check_photocell_beam(self) -> bool:
        return self._photocell_blocked

    def set_photocell_state(self, blocked: bool) -> None:
        self._photocell_blocked = blocked

    def evaluate_amperometric_limits(self, leaf1_amps: float, leaf2_amps: float) -> bool:
        """Returns True if current exceeds safe threshold (crush protection)."""
        return leaf1_amps > self.threshold or leaf2_amps > self.threshold


class IoTSerialBridgeStub(IIoTSerialBridge):
    """Bi-directional frame bridge between ESP32 and Arduino Nano."""

    def transmit_command_to_nano(self, cmd: GateCommand) -> bool:
        frame = build_frame(cmd.opcode, cmd.command_name.encode("utf-8"))
        # In production, writes byte stream to SoftwareSerial on pins D11/D12
        return len(frame) > 0

    def parse_incoming_telemetry(self, raw_bytes: bytes) -> Optional[GateTelemetrySnapshot]:
        res = parse_frame(raw_bytes)
        if not res:
            return None
        # Returns deserialized telemetry snapshot
        return GateTelemetrySnapshot(
            timestamp=datetime.utcnow(),
            motion_state=GateMotionState.OPENED,
            leaf1=LeafTelemetry(1, 0.0, 0.0, 100.0, False),
            leaf2=LeafTelemetry(2, 0.0, 0.0, 100.0, False),
            flashing_light_active=False,
            electric_lock_active=False,
            photocell_beam_blocked=False,
            active_alarm=AlarmCause.NONE,
            cycle_count=1420,
        )
