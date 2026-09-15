from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from champ_tableops.manipulation.mujoco_pick_place import run_pick_place
from champ_tableops.reasoning.command_parser import (
    UnsupportedCommandError,
    parse_command,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CHAMP TableOps Milestone 3 natural-language robotics demo."
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="Natural-language task, e.g. Set the plate.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without opening the MuJoCo viewer.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Do not pace simulation steps in real time.",
    )
    args = parser.parse_args()

    command = " ".join(args.command).strip()
    if not command:
        command = input("Command: ").strip()

    print("\n" + "=" * 54)
    print("                 CHAMP TableOps")
    print("=" * 54)
    print(f"Command: {command}")

    try:
        intent = parse_command(command)
    except UnsupportedCommandError as exc:
        print("[TableOps] REASON: command not supported")
        print(f"[TableOps] ERROR: {exc}")
        return 2

    print("[TableOps] REASON: interpreting request")
    print(f"[TableOps] INTENT: {intent.action}")
    print(f"[TableOps] OBJECT: {intent.object_name}")
    print(f"[TableOps] TARGET: {intent.target}")
    print("[TableOps] PLAN: generated manipulation sequence")
    print("[TableOps] ACT: executing MuJoCo manipulation")

    result = run_pick_place(
        render=not args.headless,
        realtime=not args.fast and not args.headless,
        verbose=True,
    )

    print(f"[TableOps] FINAL POSITION: {result.final_position}")
    print(f"[TableOps] TARGET POSITION: {result.target_position}")
    print(f"[TableOps] PLANAR ERROR: {result.planar_error:.4f} m")

    if result.success:
        print("[TableOps] VERIFY: placement accepted")
        print("[TableOps] SUCCESS")
        print("MILESTONE 3: SUCCESS")
        return 0

    print("[TableOps] VERIFY: placement rejected")
    print("[TableOps] FAILED")
    print("MILESTONE 3: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
