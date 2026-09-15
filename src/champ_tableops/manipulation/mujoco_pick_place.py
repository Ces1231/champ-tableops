from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

import mujoco
import numpy as np


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[3] / "simulation" / "table_scene_v2.xml"
)


@dataclass(frozen=True)
class PickPlaceResult:
    success: bool
    final_position: tuple[float, float, float]
    target_position: tuple[float, float, float]
    planar_error: float
    phases: tuple[str, ...]


class PickPlaceController:
    """Deterministic Milestone 2 controller for the CHAMP TableOps demo.

    The robot moves through MuJoCo position actuators. The plate free joint is never
    rewritten by this controller. At grasp time, a site-to-site weld constraint is
    enabled to model a stable closed gripper; it is disabled again at release.
    """

    def __init__(
        self,
        model: mujoco.MjModel,
        data: mujoco.MjData,
        *,
        viewer: Any | None = None,
        realtime: bool = False,
        verbose: bool = True,
    ) -> None:
        self.model = model
        self.data = data
        self.viewer = viewer
        self.realtime = realtime
        self.verbose = verbose
        self.phases: list[str] = []

        self.actuators = {
            name: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
            for name in (
                "x_position",
                "y_position",
                "z_position",
                "left_grip",
                "right_grip",
            )
        }
        self.joints = {
            name: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
            for name in (
                "slide_x",
                "slide_y",
                "slide_z",
                "left_finger_joint",
                "right_finger_joint",
            )
        }
        self.plate_body = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_BODY, "plate"
        )
        self.target_site = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_SITE, "target"
        )
        self.grasp_site = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_SITE, "grasp_site"
        )
        self.plate_grasp_site = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_SITE, "plate_grasp_site"
        )
        self.grasp_weld = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_EQUALITY, "grasp_weld"
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
        qpos_address = self.model.jnt_qposadr[joint_id]
        return float(self.data.qpos[qpos_address])

    def _joint_velocity(self, name: str) -> float:
        joint_id = self.joints[name]
        dof_address = self.model.jnt_dofadr[joint_id]
        return float(self.data.qvel[dof_address])

    def _set_controls(
        self,
        *,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
        grip: float | None = None,
    ) -> dict[str, float]:
        targets: dict[str, float] = {}
        if x is not None:
            self.data.ctrl[self.actuators["x_position"]] = x
            targets["slide_x"] = x
        if y is not None:
            self.data.ctrl[self.actuators["y_position"]] = y
            targets["slide_y"] = y
        if z is not None:
            self.data.ctrl[self.actuators["z_position"]] = z
            targets["slide_z"] = z
        if grip is not None:
            self.data.ctrl[self.actuators["left_grip"]] = grip
            self.data.ctrl[self.actuators["right_grip"]] = grip
            targets["left_finger_joint"] = grip
            targets["right_finger_joint"] = grip
        return targets

    def _move(
        self,
        *,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
        grip: float | None = None,
        tolerance: float = 0.006,
        velocity_tolerance: float = 0.04,
        max_steps: int = 1800,
    ) -> None:
        targets = self._set_controls(x=x, y=y, z=z, grip=grip)
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
            f"Manipulator failed to converge. targets={targets}, current={current}"
        )

    def _grasp_alignment_error(self) -> float:
        mujoco.mj_forward(self.model, self.data)
        return float(
            np.linalg.norm(
                self.data.site_xpos[self.grasp_site]
                - self.data.site_xpos[self.plate_grasp_site]
            )
        )

    def run(self) -> PickPlaceResult:
        self._announce("PERCEIVE: settle scene and locate plate")
        self._set_controls(x=0.10, y=0.0, z=-0.18, grip=0.0)
        self._step(250)

        self._announce("PLAN: approach plate")
        self._move(x=0.25, y=0.0, z=-0.25, grip=0.0)

        self._announce("ACT: descend to grasp pose")
        self._move(z=-0.445)

        alignment_error = self._grasp_alignment_error()
        if alignment_error > 0.035:
            gripper_pos = tuple(
                round(float(v), 4) for v in self.data.site_xpos[self.grasp_site]
            )
            plate_pos = tuple(
                round(float(v), 4)
                for v in self.data.site_xpos[self.plate_grasp_site]
            )
            raise RuntimeError(
                "Gripper is not aligned with plate: "
                f"error={alignment_error:.4f} m, "
                f"gripper={gripper_pos}, plate={plate_pos}, "
                f"slide_z={self._joint_position('slide_z'):.4f}"
            )

        self._announce("ACT: close gripper")
        self._move(grip=0.04)

        self._announce("ACT: latch simulated grasp")
        self.data.eq_active[self.grasp_weld] = 1
        mujoco.mj_forward(self.model, self.data)
        self._step(120)

        self._announce("ACT: lift plate")
        self._move(z=-0.20)

        self._announce("ACT: transfer plate to target")
        self._move(x=0.95, y=0.0)

        self._announce("ACT: lower plate")
        self._move(z=-0.445)
        self._step(100)

        self._announce("ACT: release plate")
        self.data.eq_active[self.grasp_weld] = 0
        self._move(grip=0.0)
        self._step(300)

        self._announce("ACT: retreat")
        self._move(z=-0.22)
        self._move(x=0.75)

        self._announce("VERIFY: measure final placement")
        mujoco.mj_forward(self.model, self.data)
        final = self.data.xpos[self.plate_body].copy()
        target = self.data.site_xpos[self.target_site].copy()
        planar_error = float(np.linalg.norm(final[:2] - target[:2]))
        success = planar_error < 0.04 and final[2] < 0.13

        self._announce("SUCCESS" if success else "FAILED")
        return PickPlaceResult(
            success=success,
            final_position=tuple(float(v) for v in final),
            target_position=tuple(float(v) for v in target),
            planar_error=planar_error,
            phases=tuple(self.phases),
        )


def _execute(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    *,
    viewer: Any | None,
    realtime: bool,
    verbose: bool,
) -> PickPlaceResult:
    controller = PickPlaceController(
        model,
        data,
        viewer=viewer,
        realtime=realtime,
        verbose=verbose,
    )
    return controller.run()


def run_pick_place(
    model_path: str | Path = DEFAULT_MODEL_PATH,
    *,
    render: bool = False,
    realtime: bool = False,
    verbose: bool = True,
) -> PickPlaceResult:
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
        )

    from mujoco import viewer as mujoco_viewer

    # On WSLg, viewer.close() can close the window but block the Python process.
    # Leave process teardown to the CLI/demo entry point after it flushes output.
    viewer = mujoco_viewer.launch_passive(model, data)
    return _execute(
        model,
        data,
        viewer=viewer,
        realtime=realtime,
        verbose=verbose,
    )
