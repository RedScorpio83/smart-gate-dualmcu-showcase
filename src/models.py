"""Data Models and Telemetry Schemas for SmartGate Dual-MCU Platform."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class GateMotionState(str, Enum):
    CLOSED = "CLOSED"
    PRE_FLASHING = "PRE_FLASHING"
    HAMMER_STRIKE = "HAMMER_STRIKE"
    OPENING_LEAF1 = "OPENING_LEAF1"
    OPENING_BOTH = "OPENING_BOTH"
    OPENED = "OPENED"
    PAUSE_WORK = "PAUSE_WORK"  # Tempo Chiusura Automatica (TCA)
    CLOSING_LEAF2 = "CLOSING_LEAF2"
    CLOSING_BOTH = "CLOSING_BOTH"
    OBSTACLE_SAFETY_REVERSAL = "OBSTACLE_SAFETY_REVERSAL"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class AlarmCause(str, Enum):
    NONE = "NONE"
    PHOTOCELL_OBSTACLE = "PHOTOCELL_OBSTACLE"
    AMPEROMETRIC_SPIKE_LEAF1 = "AMPEROMETRIC_SPIKE_LEAF1"
    AMPEROMETRIC_SPIKE_LEAF2 = "AMPEROMETRIC_SPIKE_LEAF2"
    MOTOR_TIMEOUT = "MOTOR_TIMEOUT"


@dataclass
class LeafTelemetry:
    """Instantaneous operational metrics for a single gate leaf."""
    leaf_id: int  # 1 or 2
    pwm_power_pct: float
    current_amps: float
    estimated_position_pct: float  # 0.0 (fully closed) to 100.0 (fully open)
    is_moving: bool


@dataclass
class GateTelemetrySnapshot:
    """Full system state telemetry emitted from Arduino Nano to ESP32."""
    timestamp: datetime
    motion_state: GateMotionState
    leaf1: LeafTelemetry
    leaf2: LeafTelemetry
    flashing_light_active: bool
    electric_lock_active: bool
    photocell_beam_blocked: bool
    active_alarm: AlarmCause
    cycle_count: int


@dataclass
class GateCommand:
    """Instruction sent from ESP32 / Home Assistant / Frigate AI to the real-time core."""
    opcode: int
    command_name: str  # e.g., 'STEP_STEP', 'PEDESTRIAN', 'EMERGENCY_HALT'
    source: str        # e.g., 'FRIGATE_AI_CAR_DETECTION', 'WEB_UI', 'RF_433MHZ'
    timestamp: datetime = field(default_factory=datetime.utcnow)
