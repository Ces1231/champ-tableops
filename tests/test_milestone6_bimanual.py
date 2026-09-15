from champ_tableops.manipulation.mujoco_bimanual import run_bimanual_table_setting


def test_bimanual_controller_places_two_plates():
    result = run_bimanual_table_setting(
        render=False,
        realtime=False,
        verbose=False,
    )

    assert result.success is True
    assert result.left.planar_error < 0.04
    assert result.right.planar_error < 0.04
    assert result.left.name == "plate_left"
    assert result.right.name == "plate_right"
    assert "ACT: coordinated transfer to two place settings" in result.phases


def test_bimanual_offset_fails_without_correction():
    result = run_bimanual_table_setting(
        render=False,
        realtime=False,
        verbose=False,
        right_placement_offset_x=0.10,
        correct_if_needed=False,
    )

    assert result.success is False
    assert result.left.planar_error < 0.04
    assert result.right.planar_error >= 0.04
    assert result.right.correction_applied is False


def test_bimanual_verify_correct_recovers_right_plate():
    result = run_bimanual_table_setting(
        render=False,
        realtime=False,
        verbose=False,
        right_placement_offset_x=0.10,
        correct_if_needed=True,
    )

    assert result.success is True
    assert result.left.planar_error < 0.04
    assert result.right.initial_planar_error is not None
    assert result.right.initial_planar_error >= 0.04
    assert result.right.correction_applied is True
    assert result.right.planar_error < 0.04
    assert result.left.correction_applied is False
    assert "CORRECT: right manipulator repositions plate" in result.phases
