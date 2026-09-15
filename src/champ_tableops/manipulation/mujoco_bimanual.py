from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

import mujoco
import numpy as np


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[3] / "simulation" / "table_scene_bimanual.xml"
)


@dataclass(frozen=True)
class PlatePlacement:
    name: str
    final_position: tuple[float, float, float]
    target_position: tuple[float, float, float]
    planar_error: float
    initial_planar_error: float | None = None
    correction_applied: bool = False


@dataclass(frozen=True)
class BimanualResult:
    success: bool
    left: PlatePlacement
    right: PlatePlacement
    phases: tuple[str, ...]


class BimanualController:
    """Coordinate two independent MuJoCo manipulators in one table-setting scene."""

    ARMS = ("left", "right")

    def __init__(
        self,
        model: mujoco.MjModel,
        data: mujoco.MjData,
        *,
        viewer: Any | None = None,
        realtime: bool = False,
        verbose: bool = True,
        right_placement_offset_x: float = 0.0,
        correct_if_needed: bool = False,
        correction_threshold: float = 0.04,
    ) -> None:
        self.model = model
        self.data = data
        self.viewer = viewer
        self.realtime = realtime
        self.verbose = verbose
        self.right_placement_offset_x = right_placement_offset_x
        self.correct_if_needed = correct_if_needed
        self.correction_threshold = correction_threshold
        self.phases: list[str] = []

        self.actuators: dict[str, int] = {}
        self.joints: dict[str, int] = {}
        self.plate_bodies: dict[str, int] = {}
        self.target_sites: dict[str, int] = {}
        self.grasp_sites: dict[str, int] = {}
        self.plate_grasp_sites: dict[str, int] = {}
        self.grasp_welds: dict[str, int] = {}

        for arm in self.ARMS:
            for actuator in ("x_position", "y_position", "z_position", "grip_a", "grip_b"):
                name = f"{arm}_{actuator}"
                self.actuators[name] = mujoco.mj_name2id(
                    model, mujoco.mjtObj.mjOBJ_ACTUATOR, name
                )

            for joint in (
                "slide_x",
                "slide_y",
                "slide_z",
                "finger_a_joint",
                "finger_b_joint",
            ):
                name = f"{arm}_{joint}"
                self.joints[name] = mujoco.mj_name2id(
                    model, mujoco.mjtObj.mjOBJ_JOINT, name
                )

            self.plate_bodies[arm] = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_BODY, f"plate_{arm}"
            )
            self.target_sites[arm] = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_SITE, f"target_{arm}"
            )
            self.grasp_sites[arm] = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_SITE, f"{arm}_grasp_site"
            )
            self.plate_grasp_sites[arm] = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_SITE, f"plate_{arm}_grasp_site"
            )
            self.grasp_welds[arm] = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_EQUALITY, f"{arm}_grasp_weld"
            )

    def _announce(self, phase: str) -> None:
        self.phases.append(phase)
        if self.verbose:
            print(f"[TableOps] {phase}")

    def _step(self, steps: int = 1) -> None:
        for _ in range(steps):
            mujoco.mj_step(self.model, self.data)
            if self.viewer is not None:
                self.viewer.sync()
            if self.realtime:
                time.sleep(self.model.opt.timestep)

    def _joint_position(self, name: str) -> float:
        joint_id = self.joints[name]
        return float(self.data.qpos[self.model.jnt_qposadr[joint_id]])

    def _joint_velocity(self, name: str) -> float:
        joint_id = self.joints[name]
        return float(self.data.qvel[self.model.jnt_dofadr[joint_id]])

    def _set_arm_controls(
        self,
        arm: str,
        *,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
        grip: float | None = None,
    ) -> dict[str, float]:
        targets: dict[str, float] = {}
        if x is not None:
            self.data.ctrl[self.actuators[f"{arm}_x_position"]] = x
            targets[f"{arm}_slide_x"] = x
        if y is not None:
            self.data.ctrl[self.actuators[f"{arm}_y_position"]] = y
            targets[f"{arm}_slide_y"] = y
        if z is not None:
            self.data.ctrl[self.actuators[f"{arm}_z_position"]] = z
            targets[f"{arm}_slide_z"] = z
        if grip is not None:
            self.data.ctrl[self.actuators[f"{arm}_grip_a"]] = grip
            self.data.ctrl[self.actuators[f"{arm}_grip_b"]] = grip
            targets[f"{arm}_finger_a_joint"] = grip
            targets[f"{arm}_finger_b_joint"] = grip
        return targets

    def _move(
        self,
        commands: dict[str, dict[str, float]],
        *,
        tolerance: float = 0.006,
        velocity_tolerance: float = 0.04,
        max_steps: int = 1800,
    ) -> None:
        targets: dict[str, float] = {}
        for arm, command in commands.items():
            targets.update(self._set_arm_controls(arm, **command))

        for _ in range(max_steps):
            self._step()
            if all(
                abs(self._joint_position(joint_name) - target) <= tolerance
                and abs(self._joint_velocity(joint_name)) <= velocity_tolerance
                for joint_name, target in targets.items()
            ):
                return

        current = {
            name: {
                "q": round(self._joint_position(name), 4),
                "qd": round(self._joint_velocity(name), 4),
            }
            for name in targets
        }
        raise RuntimeError(
            f"Bimanual manipulator failed to converge. targets={targets}, current={current}"
        )

    def _alignment_error(self, arm: str) -> float:
        mujoco.mj_forward(self.model, self.data)
        return float(
            np.linalg.norm(
                self.data.site_xpos[self.grasp_sites[arm]]
                - self.data.site_xpos[self.plate_grasp_sites[arm]]
            )
        )

    def _placement_state(self, arm: str) -> tuple[np.ndarray, np.ndarray, float]:
        mujoco.mj_forward(self.model, self.data)
        final = self.data.xpos[self.plate_bodies[arm]].copy()
        target = self.data.site_xpos[self.target_sites[arm]].copy()
        error = float(np.linalg.norm(final[:2] - target[:2]))
        return final, target, error

    def run(self) -> BimanualResult:
        both = self.ARMS

        self._announce("PERCEIVE: locate two plates and two place settings")
        for arm in both:
            self._set_arm_controls(arm, x=0.10, y=0.0, z=-0.18, grip=0.0)
        self._step(250)

        self._announce("PLAN: coordinate left and right manipulators")
        self._move(
            {arm: {"x": 0.25, "y": 0.0, "z": -0.25, "grip": 0.0} for arm in both}
        )

        self._announce("ACT: both manipulators descend to grasp poses")
        self._move({arm: {"z": -0.445} for arm in both})

        for arm in both:
            error = self._alignment_error(arm)
            if error > 0.035:
                raise RuntimeError(
                    f"{arm} gripper is not aligned with its plate: error={error:.4f} m"
                )

        self._announce("ACT: both grippers close")
        self._move({arm: {"grip": 0.04} for arm in both})

        self._announce("ACT: latch both simulated grasps")
        for arm in both:
            self.data.eq_active[self.grasp_welds[arm]] = 1
        mujoco.mj_forward(self.model, self.data)
        self._step(120)

        self._announce("ACT: lift both plates")
        self._move({arm: {"z": -0.20} for arm in both})

        self._announce("ACT: coordinated transfer to two place settings")
        self._move(
            {
                "left": {"x": 0.95, "y": 0.0},
                "right": {"x": 0.95 + self.right_placement_offset_x, "y": 0.0},
            }
        )

        self._announce("ACT: lower both plates")
        self._move({arm: {"z": -0.445} for arm in both})
        self._step(100)

        left_initial: float | None = None
        right_initial: float | None = None
        left_corrected = False
        right_corrected = False

        if self.correct_if_needed:
            self._announce("VERIFY: inspect both placements before release")
            _, _, left_initial = self._placement_state("left")
            _, _, right_initial = self._placement_state("right")
            self._announce(
                "VERIFY: left error "
                f"{left_initial:.4f} m; right error {right_initial:.4f} m"
            )

            if left_initial >= self.correction_threshold:
                self._announce("CORRECT: left manipulator repositions plate")
                self._move({"left": {"z": -0.20}})
                self._move({"left": {"x": 0.95, "y": 0.0}})
                self._move({"left": {"z": -0.445}})
                self._step(100)
                left_corrected = True

            if right_initial >= self.correction_threshold:
                self._announce("CORRECT: right manipulator repositions plate")
                self._move({"right": {"z": -0.20}})
                self._move({"right": {"x": 0.95, "y": 0.0}})
                self._move({"right": {"z": -0.445}})
                self._step(100)
                right_corrected = True

            _, _, left_check = self._placement_state("left")
            _, _, right_check = self._placement_state("right")
            self._announce(
                "VERIFY: corrected left error "
                f"{left_check:.4f} m; right error {right_check:.4f} m"
            )

        self._announce("ACT: release both plates")
        for arm in both:
            self.data.eq_active[self.grasp_welds[arm]] = 0
        self._move({arm: {"grip": 0.0} for arm in both})
        self._step(300)

        self._announce("ACT: both manipulators retreat")
        self._move({arm: {"z": -0.22} for arm in both})
        self._move({arm: {"x": 0.75} for arm in both})

        self._announce("VERIFY: measure both final placements")
        left_final, left_target, left_error = self._placement_state("left")
        right_final, right_target, right_error = self._placement_state("right")

        left_success = left_error < self.correction_threshold and left_final[2] < 0.13
        right_success = right_error < self.correction_threshold and right_final[2] < 0.13
        success = left_success and right_success

        self._announce("SUCCESS" if success else "FAILED")
        return BimanualResult(
            success=success,
            left=PlatePlacement(
                name="plate_left",
                final_position=tuple(float(v) for v in left_final),
                target_position=tuple(float(v) for v in left_target),
                planar_error=left_error,
                initial_planar_error=left_initial,
                correction_applied=left_corrected,
            ),
            right=PlatePlacement(
                name="plate_right",
                final_position=tuple(float(v) for v in right_final),
                target_position=tuple(float(v) for v in right_target),
                planar_error=right_error,
                initial_planar_error=right_initial,
                correction_applied=right_corrected,
            ),
            phases=tuple(self.phases),
        )


def _execute(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    *,
    viewer: Any | None,
    realtime: bool,
    verbose: bool,
    right_placement_offset_x: float,
    correct_if_needed: bool,
) -> BimanualResult:
    return BimanualController(
        model,
        data,
        viewer=viewer,
        realtime=realtime,
        verbose=verbose,
        right_placement_offset_x=right_placement_offset_x,
        correct_if_needed=correct_if_needed,
    ).run()


def run_bimanual_table_setting(
    model_path: str | Path = DEFAULT_MODEL_PATH,
    *,
    render: bool = False,
    realtime: bool = False,
    verbose: bool = True,
    right_placement_offset_x: float = 0.0,
    correct_if_needed: bool = False,
) -> BimanualResult:
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    if not render:
        return _execute(
            model,
            data,
            viewer=None,
            realtime=realtime,
            verbose=verbose,
            right_placement_offset_x=right_placement_offset_x,
            correct_if_needed=correct_if_needed,
        )

    from mujoco import viewer as mujoco_viewer

    # WSLg can block in viewer.close(); the CLI hard-exits visual mode after output.
    viewer = mujoco_viewer.launch_passive(model, data)
    return _execute(
        model,
        data,
        viewer=viewer,
        realtime=realtime,
        verbose=verbose,
        right_placement_offset_x=right_placement_offset_x,
        correct_if_needed=correct_if_needed,
    )
