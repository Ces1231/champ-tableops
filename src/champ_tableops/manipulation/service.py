from dataclasses import dataclass


@dataclass(frozen=True)
class ManipulationResult:
    success: bool
    action: str
    detail: str = ""


def execute_action(action: str) -> ManipulationResult:
    return ManipulationResult(
        success=False,
        action=action,
        detail="Manipulator adapter not connected yet.",
    )
