from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from champ_tableops.manipulation.mujoco_pick_place import run_pick_place


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CHAMP TableOps Milestone 2 robotic pick-and-place demo."
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

    print("CHAMP TableOps - Milestone 2")
    print("Command: Set the plate.")
    print("Workflow: PERCEIVE -> PLAN -> ACT -> VERIFY")

    result = run_pick_place(
        render=not args.headless,
        realtime=not args.fast and not args.headless,
        verbose=True,
    )

    print(f"Final plate position : {result.final_position}")
    print(f"Target position      : {result.target_position}")
    print(f"Planar error         : {result.planar_error:.4f} m")
    print("MILESTONE 2: SUCCESS" if result.success else "MILESTONE 2: FAILED")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
