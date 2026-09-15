import pytest

from champ_tableops.reasoning.command_parser import (
    UnsupportedCommandError,
    parse_command,
)


@pytest.mark.parametrize(
    "command",
    [
        "Set the plate.",
        "Place the plate.",
        "Move the plate to the table setting.",
        "Put the plate in place.",
        "Set the table for one.",
    ],
)
def test_supported_commands_map_to_plate_place_task(command: str):
    intent = parse_command(command)

    assert intent.action == "place"
    assert intent.object_name == "plate"
    assert intent.target == "place_setting_1"


def test_two_place_setting_maps_to_bimanual_task():
    intent = parse_command("Set the table for two.")

    assert intent.action == "set_table"
    assert intent.object_name == "plates"
    assert intent.target == "place_settings_1_2"


def test_unknown_command_is_rejected():
    with pytest.raises(UnsupportedCommandError):
        parse_command("Wash the dishes.")
