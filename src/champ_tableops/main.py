from champ_tableops.planning.service import build_demo_plan
from champ_tableops.verification.service import verify_demo_result


def main() -> None:
    command = "Set the table for two."
    print(f"CHAMP TableOps | command={command!r}")

    plan = build_demo_plan(command)
    print(f"Plan contains {len(plan)} step(s):")
    for index, step in enumerate(plan, start=1):
        print(f"  {index}. {step}")

    result = verify_demo_result(expected_steps=len(plan), completed_steps=0)
    print(f"Verification status: {result}")


if __name__ == "__main__":
    main()
