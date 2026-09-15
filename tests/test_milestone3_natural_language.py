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


def test_two_place_setting_is_deferred():
    with pytest.raises(UnsupportedCommandError, match="Two-place"):
        parse_command("Set the table for two.")


def test_unknown_command_is_rejected():
    with pytest.raises(UnsupportedCommandError):
        parse_command("Wash the dishes.")
