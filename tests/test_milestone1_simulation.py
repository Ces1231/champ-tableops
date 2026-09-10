from pathlib import Path

import mujoco
import numpy as np


def test_plate_reaches_target():
    model_path = (
        Path(__file__).resolve().parents[1]
        / "simulation"
        / "table_scene.xml"
    )

    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    plate_body = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_BODY,
        "plate",
    )

    target_site = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_SITE,
        "target",
    )

    mujoco.mj_forward(model, data)

    target = data.site_xpos[target_site].copy()

    joint_id = model.body_jntadr[plate_body]
    qpos_adr = model.jnt_qposadr[joint_id]

    data.qpos[qpos_adr:qpos_adr + 3] = target
    mujoco.mj_forward(model, data)

    final = data.xpos[plate_body].copy()

    assert np.linalg.norm(final - target) < 0.01
