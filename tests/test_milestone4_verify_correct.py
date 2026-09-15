from champ_tableops.manipulation.mujoco_pick_place import run_pick_place


def test_offset_placement_fails_without_correction():
    result = run_pick_place(
        render=False,
        realtime=False,
        verbose=False,
        placement_offset_x=0.10,
        correct_if_needed=False,
    )

    assert not result.success
    assert result.planar_error >= 0.04
    assert not result.correction_applied


def test_verify_correct_recovers_offset_placement():
    result = run_pick_place(
        render=False,
        realtime=False,
        verbose=False,
        placement_offset_x=0.10,
        correct_if_needed=True,
    )

    assert result.success
    assert result.initial_planar_error is not None
    assert result.initial_planar_error >= 0.04
    assert result.correction_applied
    assert result.planar_error < 0.04
    assert any(phase.startswith("VERIFY: placement outside tolerance") for phase in result.phases)
    assert "CORRECT: reposition plate to target" in result.phases
    assert any(phase.startswith("VERIFY: correction within tolerance") for phase in result.phases)
    assert result.phases[-1] == "SUCCESS"
