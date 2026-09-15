from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TaskIntent:
    action: str
    object_name: str
    target: str
    source_command: str


class UnsupportedCommandError(ValueError):
    """Raised when the deterministic parser cannot map a command safely."""


def parse_command(command: str) -> TaskIntent:
    """Map supported table-setting commands into the verified controller contract."""
    normalized = re.sub(r"[^a-z0-9 ]+", " ", command.lower())
    normalized = " ".join(normalized.split())

    if not normalized:
        raise UnsupportedCommandError("Command is empty.")

    supported_action = any(
        token in normalized.split()
        for token in ("set", "place", "move", "put")
    )

    two_setting_requested = (
        "table" in normalized
        and ("for two" in normalized or "for 2" in normalized)
    )
    if supported_action and two_setting_requested:
        return TaskIntent(
            action="set_table",
            object_name="plates",
            target="place_settings_1_2",
            source_command=command,
        )

    plate_requested = "plate" in normalized
    single_setting_requested = (
        "table" in normalized
        and ("for one" in normalized or "for 1" in normalized)
    )

    if supported_action and (plate_requested or single_setting_requested):
        return TaskIntent(
            action="place",
            object_name="plate",
            target="place_setting_1",
            source_command=command,
        )

    raise UnsupportedCommandError(
        "Supported commands include 'Set the plate.', 'Set the table for one.', "
        "and 'Set the table for two.'"
    )
