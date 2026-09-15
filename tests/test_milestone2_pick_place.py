from champ_tableops.manipulation.mujoco_pick_place import run_pick_place


def test_robot_moves_plate_to_target_without_rewriting_plate_qpos():
    result = run_pick_place(render=False, realtime=False, verbose=False)

    assert result.success
    assert result.planar_error < 0.04
    assert "ACT: lift plate" in result.phases
    assert "ACT: transfer plate to target" in result.phases
    assert result.phases[-1] == "SUCCESS"
