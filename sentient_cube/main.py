from __future__ import annotations

import argparse
import json

from sentient_cube.core import SentientCubeCore
from sentient_cube.control.hardware import HardwareConfig
from sentient_cube.models import Mode


def run_hardware_self_test(core: SentientCubeCore) -> dict:
    core.set_mode(Mode.FOCUS, reason="self_test")
    core.hardware.move_gimbal(20.0, 0.0)
    core.hardware.set_breath(45.0, speed=1.0)
    core.hardware.set_laser(True)
    core.hardware.set_laser(False)
    core.set_mode(Mode.AMBIENT, reason="self_test_done")
    return core.status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sentient Cube local core runtime")
    parser.add_argument("--db", default="spatial_memory.db", help="Path to sqlite database")
    parser.add_argument("--command", default="", help="One-shot text command")
    parser.add_argument("--detect-image", default="", help="Run object detection for one image")
    parser.add_argument("--location-hint", default="桌面区域", help="Location label for detected objects")
    parser.add_argument(
        "--hardware-backend",
        default="mock",
        choices=["mock", "serial", "pca9685"],
        help="Hardware backend type",
    )
    parser.add_argument("--serial-port", default="COM3", help="Serial port for Arduino backend")
    parser.add_argument("--serial-baudrate", type=int, default=115200, help="Serial baudrate")
    parser.add_argument("--hardware-self-test", action="store_true", help="Run hardware self-test and exit")
    args = parser.parse_args()

    hardware_config = HardwareConfig(
        backend=args.hardware_backend,
        serial_port=args.serial_port,
        serial_baudrate=args.serial_baudrate,
    )
    core = SentientCubeCore(db_path=args.db, hardware_config=hardware_config)
    try:
        if args.hardware_self_test:
            print(json.dumps(run_hardware_self_test(core), ensure_ascii=False, indent=2))
            return

        if args.command:
            print(json.dumps(core.process_text(args.command), ensure_ascii=False, indent=2))
            print(json.dumps(core.status(), ensure_ascii=False, indent=2))
            return

        if args.detect_image:
            print(
                json.dumps(
                    core.detect_and_remember(args.detect_image, location_hint=args.location_hint),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            print(json.dumps(core.status(), ensure_ascii=False, indent=2))
            return

        print("Sentient Cube core started. Type command and press Enter, type 'exit' to quit.")
        while True:
            text = input("> ").strip()
            if text.lower() in {"exit", "quit"}:
                break
            if not text:
                payload = core.tick()
            else:
                payload = core.process_text(text)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    finally:
        core.close()


if __name__ == "__main__":
    main()
