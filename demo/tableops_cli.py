from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from champ_tableops.manipulation.mujoco_pick_place import run_pick_place
from champ_tableops.reasoning.command_parser import UnsupportedCommandError
from champ_tableops.reasoning.openvino_reasoner import (
    OpenVINOReasoningError,
    reason_command,
)


def _finish(exit_code: int, *, visual: bool) -> int:
    """Return normally headless; hard-exit visual mode to avoid WSLg GLFW hangs."""
    sys.stdout.flush()
    sys.stderr.flush()
    if visual:
        os._exit(exit_code)
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CHAMP TableOps natural-language Physical AI demo."
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
    parser.add_argument(
        "--demo-correction",
        action="store_true",
        help=(
            "Inject a 10 cm placement error, verify it, and physically correct "
            "the plate before release."
        ),
    )
    parser.add_argument(
        "--reasoner",
        choices=("auto", "deterministic", "openvino"),
        default=os.environ.get("CHAMP_TABLEOPS_REASONER", "auto"),
        help=(
            "Reasoning backend. auto uses OpenVINO when a model is configured and "
            "otherwise preserves the deterministic fallback."
        ),
    )
    parser.add_argument(
        "--openvino-model",
        default=os.environ.get("CHAMP_TABLEOPS_OPENVINO_MODEL"),
        help="Path to an OpenVINO GenAI LLM directory.",
    )
    parser.add_argument(
        "--openvino-device",
        default=os.environ.get("CHAMP_TABLEOPS_OPENVINO_DEVICE", "CPU"),
        help="OpenVINO inference device, e.g. CPU, GPU, or NPU.",
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
        reasoning = reason_command(
            command,
            backend=args.reasoner,
            model_path=args.openvino_model,
            device=args.openvino_device,
        )
        intent = reasoning.intent
    except UnsupportedCommandError as exc:
        print("[TableOps] REASON: command not supported")
        print(f"[TableOps] ERROR: {exc}")
        return 2
    except OpenVINOReasoningError as exc:
        print("[TableOps] REASON: OpenVINO reasoning unavailable")
        print(f"[TableOps] ERROR: {exc}")
        return 2

    print("[TableOps] REASON: interpreting request")
    print(f"[TableOps] REASONER: {reasoning.backend}")
    if reasoning.backend == "openvino_genai":
        print(f"[TableOps] INTEL: OpenVINO GenAI active on {args.openvino_device}")
    if reasoning.fallback_used:
        print("[TableOps] REASONER FALLBACK: deterministic")
        print(f"[TableOps] FALLBACK REASON: {reasoning.fallback_reason}")

    print(f"[TableOps] INTENT: {intent.action}")
    print(f"[TableOps] OBJECT: {intent.object_name}")
    print(f"[TableOps] TARGET: {intent.target}")
    print("[TableOps] PLAN: generated manipulation sequence")

    if args.demo_correction:
        print("[TableOps] DEMO: inject 0.10 m placement error")
        print("[TableOps] GOAL: demonstrate VERIFY -> CORRECT recovery")

    print("[TableOps] ACT: executing MuJoCo manipulation")

    result = run_pick_place(
        render=not args.headless,
        realtime=not args.fast and not args.headless,
        verbose=True,
        placement_offset_x=0.10 if args.demo_correction else 0.0,
        correct_if_needed=args.demo_correction,
    )

    if result.initial_planar_error is not None:
        print(
            "[TableOps] INITIAL PLANAR ERROR: "
            f"{result.initial_planar_error:.4f} m"
        )
    if args.demo_correction:
        print(
            "[TableOps] CORRECTION APPLIED: "
            f"{'yes' if result.correction_applied else 'no'}"
        )

    print(f"[TableOps] FINAL POSITION: {result.final_position}")
    print(f"[TableOps] TARGET POSITION: {result.target_position}")
    print(f"[TableOps] PLANAR ERROR: {result.planar_error:.4f} m")

    milestone = 5 if reasoning.backend == "openvino_genai" else (
        4 if args.demo_correction else 3
    )

    if result.success:
        print("[TableOps] VERIFY: placement accepted")
        print("[TableOps] SUCCESS")
        print(f"MILESTONE {milestone}: SUCCESS")
        return _finish(0, visual=not args.headless)

    print("[TableOps] VERIFY: placement rejected")
    print("[TableOps] FAILED")
    print(f"MILESTONE {milestone}: FAILED")
    return _finish(1, visual=not args.headless)


if __name__ == "__main__":
    raise SystemExit(main())
