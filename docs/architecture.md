# CHAMP TableOps Architecture

## Closed-Loop Physical AI Pipeline

```text
Voice / Text Command
        |
        v
Input / Voice AI
        |
        v
Perception
        |
        v
Reasoning
        |
        v
Planning
        |
        v
Manipulation
        |
        v
Verification
        |
 failure +-----> Correction / Re-plan
```

## Module Responsibilities

### perception
Transforms simulator/vision state into a normalized world-state representation.

### reasoning
Interprets user intent and derives the desired target state.

### planning
Converts the target state into ordered manipulation actions.

### manipulation
Executes robot actions through the selected simulator/VLA interface.

### verification
Compares observed outcomes against expected state and reports deviations.

### voice
Optional Speechmatics adapter that converts speech into text commands.

## Design Principles

1. Simulation first.
2. Keep challenge-specific SDK code behind adapters.
3. Separate reasoning from physical execution.
4. Verify every action that materially changes the scene.
5. Make demo-critical paths observable and loggable.
