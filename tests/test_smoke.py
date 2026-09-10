from champ_tableops.planning.service import build_demo_plan
from champ_tableops.verification.service import verify_demo_result


def test_table_setting_plan_contains_verification() -> None:
    plan = build_demo_plan("Set the table for two.")
    assert "verify_scene" in plan


def test_incomplete_result_is_reported() -> None:
    assert verify_demo_result(expected_steps=4, completed_steps=2) == "incomplete"
