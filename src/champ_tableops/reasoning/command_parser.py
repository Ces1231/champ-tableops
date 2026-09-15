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
    """Raised when the Milestone 3 deterministic parser cannot map a command."""


def parse_command(command: str) -> TaskIntent:
    """Convert a small set of natural-language table-setting commands into a task.

    Milestone 3 intentionally uses a deterministic parser so the robotics demo remains
    reliable. A VLA/LLM reasoning layer can later emit the same TaskIntent contract.
    """
    normalized = re.sub(r"[^a-z0-9 ]+", " ", command.lower())
    normalized = " ".join(normalized.split())

    if not normalized:
        raise UnsupportedCommandError("Command is empty.")

    if "table" in normalized and ("for two" in normalized or "for 2" in normalized):
        raise UnsupportedCommandError(
            "Two-place table setting requires the future bimanual/multi-object milestone."
        )

    plate_requested = "plate" in normalized
    single_setting_requested = (
        "table" in normalized
        and ("for one" in normalized or "for 1" in normalized)
    )
    supported_action = any(
        token in normalized.split()
        for token in ("set", "place", "move", "put")
    )

    if supported_action and (plate_requested or single_setting_requested):
        return TaskIntent(
            action="place",
            object_name="plate",
            target="place_setting_1",
            source_command=command,
        )

    raise UnsupportedCommandError(
        "Supported Milestone 3 commands include 'Set the plate.' and "
        "'Set the table for one.'"
    )
