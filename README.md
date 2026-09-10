# CHAMP TableOps

**Voice-Guided Physical AI for Bimanual Table Setting**

CHAMP TableOps is a hackathon prototype for the **AI Infra Summit Hackathon 2026**.

The system is designed around a closed-loop Physical AI workflow:

**Perceive → Reason → Plan → Act → Verify → Correct**

The initial demo target is autonomous table setting in simulation using two robotic manipulators, multimodal reasoning, and optional real-time voice interaction.

## Objectives

- Observe a simulated tabletop scene.
- Identify plates, cups, utensils, napkins, and other task objects.
- Convert natural-language or spoken instructions into structured tasks.
- Plan a sequence of manipulation actions.
- Coordinate two simulated robot arms.
- Verify that the resulting scene satisfies the requested task.
- Correct failed or incomplete placements.

## Proposed Stack

- Python 3.11+
- MuJoCo or the hackathon-provided robotics simulator
- Intel OpenVINO / Intel Physical AI tooling as required by the challenge
- Multimodal/VLA model selected from official challenge resources
- Speechmatics for optional speech-to-text
- Pytest for validation
- Docker for reproducible execution

> Final Intel models, SDKs, and starter repositories should be pinned only after the official track brief is confirmed.

## Repository Layout

```text
champ-tableops/
├── .github/workflows/
├── assets/
├── demo/
├── docker/
├── docs/
├── outputs/
├── scripts/
├── simulation/
├── src/champ_tableops/
│   ├── manipulation/
│   ├── perception/
│   ├── planning/
│   ├── reasoning/
│   ├── verification/
│   └── voice/
└── tests/
```

## Quick Start

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest
$env:PYTHONPATH="src"
python -m champ_tableops.main
```

### Linux/macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest
PYTHONPATH=src python -m champ_tableops.main
```

## First Milestone

Launch the simulator and successfully move **one table object** from a start pose to a target pose.

After that baseline works, expand to bimanual coordination, multimodal reasoning, verification, and voice control.

## Demo Scenario

Example command:

> "Set the table for two."

Expected workflow:

1. Perception detects available objects and their locations.
2. Reasoning interprets the desired final scene.
3. Planning generates ordered manipulation tasks.
4. Manipulation executes pick-and-place actions.
5. Verification checks the resulting scene.
6. Correction retries or repairs failed placements.

## License

MIT License. See [LICENSE](LICENSE).
