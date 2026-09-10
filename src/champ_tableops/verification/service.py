def verify_demo_result(expected_steps: int, completed_steps: int) -> str:
    if completed_steps >= expected_steps:
        return "verified"
    return "incomplete"
