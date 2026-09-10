def interpret_intent(command: str) -> dict[str, object]:
    return {
        "command": command,
        "task": "table_setting",
        "place_settings": 2,
    }
