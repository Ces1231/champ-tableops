def build_demo_plan(command: str) -> list[str]:
    # Temporary deterministic plan until the official VLA/reasoning stack is integrated.
    if "table" not in command.lower():
        return ["inspect_scene"]

    return [
        "inspect_scene",
        "locate_place_settings",
        "place_plate_left",
        "place_plate_right",
        "place_utensils",
        "place_cups",
        "verify_scene",
    ]
