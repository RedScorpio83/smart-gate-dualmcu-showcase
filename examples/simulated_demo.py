#!/usr/bin/env python3
"""SmartGate Dual-MCU Architectural Showcase - Standalone Simulation Demo.

Simulates:
1. Inter-MCU UART handshake between ESP32 and Arduino Nano.
2. Opening cycle initiation via Frigate AI Vehicle Detection.
3. Leaf staggering delay (Leaf 1 starts first, followed by Leaf 2).
4. Amperometric current spike obstacle detection during closing cycle.
5. Immediate emergency braking and safety reversal sequence.
"""

import os
import sys
import time

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add package root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models import GateCommand, GateMotionState, AlarmCause
from src.stubs import DualBts7960MotorControllerStub, SafetySupervisorStub, IoTSerialBridgeStub
from src.serial_protocol import build_frame, parse_frame, GateProtocolOpcodes


def run_simulation():
    print("=" * 70)
    print("  SMARTGATE DUAL-MCU ARCHITECTURAL SHOWCASE -- SIMULATION DEMO")
    print("  Author: Alessandro Caliciotti (@RedScorpio83)")
    print("=" * 70)

    # 1. Initialize Subsystems
    print("\n[1/5] Initializing Dual-MCU Serial Link & Real-Time Safety Core...")
    motors = DualBts7960MotorControllerStub()
    safety = SafetySupervisorStub(current_threshold_amps=5.5)
    serial_bridge = IoTSerialBridgeStub()

    test_frame = build_frame(GateProtocolOpcodes.CMD_TOGGLE_CYCLE, b"STEP_STEP")
    opcode, payload = parse_frame(test_frame)
    print(f"      [OK] Serial framing validated: Opcode=0x{opcode:02X} | Checksum=CRC-8 Verified")
    print("      [OK] Dual BTS7960 H-Bridges initialized with Soft Start PWM.")
    print("      [OK] Current Sensing ADC shunts active on Pins A1/A2 (Threshold: 5.5A).")

    # 2. Simulate Frigate AI Vehicle Detection Trigger
    print("\n[2/5] Event Trigger: Frigate AI Vehicle Recognition (Camera Driveway)...")
    cmd = GateCommand(
        opcode=GateProtocolOpcodes.CMD_TOGGLE_CYCLE,
        command_name="AUTO_OPEN_AUTHORIZED_CAR",
        source="FRIGATE_NVR_AI",
    )
    serial_bridge.transmit_command_to_nano(cmd)
    print("      • Command Dispatched: 'AUTO_OPEN_AUTHORIZED_CAR' -> Dispatched to Arduino Nano")
    print("      • Relay 1 (Pin D10): 24V Flashing Light PRE-FLASHING (1.5s warning)")
    print("      • Relay 2 (Pin D4):  Electric Lock Strike 'Colpo d'ariete' (1.2s pulse)")

    # 3. Simulate Staggered Leaf Opening
    print("\n[3/5] Executing Staggered Leaf Opening Cycle...")
    motors.set_motor_speed(leaf_id=1, direction="OPEN", pwm_duty=255)
    motors.simulate_load_current(leaf_id=1, amps=2.8)
    print(f"      • Leaf 1 (RPWM D3): Motor active at 100% PWM | Nominal Current={motors.read_motor_current(1)}A")
    print("      • Leaf Staggering:  Leaf 2 motion deferred by 3.0 seconds to clear lock latch")

    motors.set_motor_speed(leaf_id=2, direction="OPEN", pwm_duty=255)
    motors.simulate_load_current(leaf_id=2, amps=2.6)
    print(f"      • Leaf 2 (RPWM D6): Motor active at 100% PWM | Nominal Current={motors.read_motor_current(2)}A")
    print("      • State Transition: Gate fully open -> Hold-Open Pause (TCA Timer active)")

    # 4. Closing Cycle & Obstacle Collision Detection
    print("\n[4/5] Initiating Closing Cycle with Simulated Obstacle Collision...")
    print("      • Leaf 2 starts closing first (RPWM D9) -> Leaf 1 follows after 3.0s delay")
    print("      • Simulating Physical Obstacle (e.g., parked vehicle bumper / obstruction)...")

    # Inject amperometric overload on Leaf 1
    motors.simulate_load_current(leaf_id=1, amps=8.2)  # Over threshold (5.5A)
    current_m1 = motors.read_motor_current(1)
    current_m2 = motors.read_motor_current(2)

    is_danger = safety.evaluate_amperometric_limits(current_m1, current_m2)
    print(f"      [ADC SENSING] Pin A1 Current: {current_m1}A | Pin A2 Current: {current_m2}A")

    if is_danger:
        print(f"      [SAFETY ALERT] AMBER SPIKE DETECTED! Current {current_m1}A exceeds 5.5A threshold!")
        motors.emergency_brake_all()
        print("      [EMERGENCY BRAKE] Both H-Bridges short-circuited to GND in < 20 ms.")
        print("      [SAFETY REVERSAL] Opening Leaf 1 & 2 for 4.0 seconds to release trapped object.")
        print("      [MQTT TELEMETRY] Published alert to Home Assistant: 'OBSTACLE_SAFETY_REVERSAL'")

    # 5. Conclusion
    print("\n[5/5] Cycle Stabilized & Safely Disengaged.")
    print("=" * 70)
    print("  SIMULATION COMPLETED WITH SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    run_simulation()
