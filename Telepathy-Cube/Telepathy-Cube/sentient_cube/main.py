from __future__ import annotations

import argparse
import json
import time

from sentient_cube.core import SentientCubeCore


def main() -> None:
    parser = argparse.ArgumentParser(description="Sentient Cube local core runtime")
    parser.add_argument("--db", default="spatial_memory.db", help="Path to sqlite database")
    parser.add_argument("--command", default="", help="One-shot text command")
    parser.add_argument("--detect-image", default="", help="Run object detection for one image")
    parser.add_argument("--location-hint", default="桌面区域", help="Location label for detected objects")
    args = parser.parse_args()

    core = SentientCubeCore(db_path=args.db)
    try:
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
