from pathlib import Path
import mujoco


MODEL_PATH = Path(__file__).with_name("table_scene.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
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

start = data.xpos[plate_body].copy()
target = data.site_xpos[target_site].copy()

print("CHAMP TableOps - Milestone 1")
print("Start :", start)
print("Target:", target)

joint_id = model.body_jntadr[plate_body]
qpos_adr = model.jnt_qposadr[joint_id]

data.qpos[qpos_adr:qpos_adr + 3] = target

mujoco.mj_forward(model, data)

final = data.xpos[plate_body].copy()

print("Final :", final)

distance = ((final - target) ** 2).sum() ** 0.5

print(f"Distance to target: {distance:.6f}")

if distance < 0.01:
    print("MILESTONE 1: SUCCESS")
else:
    print("MILESTONE 1: FAILED")
