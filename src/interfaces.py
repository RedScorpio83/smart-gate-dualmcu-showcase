"""Abstract Architectural Interfaces and Protocols for SmartGate Dual-MCU."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from .models import GateTelemetrySnapshot, GateCommand, GateMotionState


class IRealTimeMotorController(ABC):
    """Abstract interface for low-level BTS7960 motor drivers and PWM generation."""

    @abstractmethod
    def set_motor_speed(self, leaf_id: int, direction: str, pwm_duty: int) -> None:
        """Sets directional PWM power (0-255) on BTS7960 driver."""
        pass

    @abstractmethod
    def emergency_brake_all(self) -> None:
        """Disables all PWM outputs and short-circuits motor windings for rapid braking."""
        pass

    @abstractmethod
    def read_motor_current(self, leaf_id: int) -> float:
        """Reads instantaneous current in Amperes from ADC shunt pins A1/A2."""
        pass


class ISafetySupervisor(ABC):
    """Deterministic real-time safety monitor executing on Arduino Nano."""

    @abstractmethod
    def check_photocell_beam(self) -> bool:
        """Reads normally-closed (NC) optical safety sensors. Returns True if obstructed."""
        pass

    @abstractmethod
    def evaluate_amperometric_limits(self, leaf1_amps: float, leaf2_amps: float) -> bool:
        """Determines if motor current draw exceeds anti-crush safety envelope."""
        pass


class IIoTSerialBridge(ABC):
    """Bidirectional UART communication bridge linking Arduino Nano and ESP32."""

    @abstractmethod
    def transmit_command_to_nano(self, cmd: GateCommand) -> bool:
        """Encodes and sends framed command packet across Logic Level Converter."""
        pass

    @abstractmethod
    def parse_incoming_telemetry(self, raw_bytes: bytes) -> Optional[GateTelemetrySnapshot]:
        """Decodes telemetry frame and verifies CRC-8 integrity checksum."""
        pass


class IHomeAssistantMqttPublisher(ABC):
    """Contract for publishing telemetry to Home Assistant and responding to Frigate AI events."""

    @abstractmethod
    def publish_gate_state(self, snapshot: GateTelemetrySnapshot) -> None:
        """Broadcasts gate position, sensor state, and motion telemetry over MQTT."""
        pass

    @abstractmethod
    def handle_frigate_detection(self, camera_id: str, label: str, confidence: float) -> None:
        """Evaluates computer vision recognition event to trigger automatic opening."""
        pass
